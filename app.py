import os, json, re, uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
app=Flask(__name__)
app.config["MAX_CONTENT_LENGTH"]=10*1024*1024

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY","")
MODEL=os.getenv("OPENAI_MODEL","gpt-5")
client=OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

try:
    from google.cloud import vision
    vision_client=vision.ImageAnnotatorClient() if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") else None
except Exception:
    vision_client=None

PROFILE_FILE="local_profiles.json"
REMINDER_FILE="local_reminders.json"

def read_json(path,default):
    if not os.path.exists(path): return default
    try:
        with open(path,encoding="utf-8") as f:return json.load(f)
    except:return default

def write_json(path,data):
    with open(path,"w",encoding="utf-8") as f:json.dump(data,f,indent=2)

def ai(prompt,instructions):
    if not client: return None
    try:
        r=client.responses.create(model=MODEL,instructions=instructions,input=prompt)
        return r.output_text
    except Exception as e:
        return None

def extract_fields(text):
    def pick(pattern):
        m=re.search(pattern,text,re.I); return m.group(1).strip() if m else ""
    cat=re.search(r"\b(SC|ST|OBC|EWS|GENERAL)\b",text,re.I)
    income=pick(r"(?:annual\s*)?income\s*[:\-]?\s*(?:rs\.?|₹)?\s*([\d,]{3,})")
    return {
      "name":pick(r"(?:name|applicant name)\s*[:\-]?\s*([A-Za-z][A-Za-z .'-]{2,60})"),
      "guardian":pick(r"(?:father|mother|guardian)(?:'s)?\s*name?\s*[:\-]?\s*([A-Za-z][A-Za-z .'-]{2,60})"),
      "age":pick(r"\bage\s*[:\-]?\s*(\d{1,3})"),
      "category":cat.group(1).upper() if cat else "",
      "income":income.replace(",","") if income else "",
      "state":pick(r"\bstate\s*[:\-]?\s*([A-Za-z ]{3,50})"),
      "district":pick(r"\bdistrict\s*[:\-]?\s*([A-Za-z ]{3,50})")
    }

@app.route("/")
def home(): return render_template("index.html")
@app.route("/ai-manager")
def manager(): return render_template("ai-manager.html")
@app.route("/eligibility")
def eligibility_page(): return render_template("eligibility.html")
@app.route("/document-engine")
def document_page(): return render_template("document-engine.html")

@app.post("/api/chat")
def chat():
    data=request.get_json() or {}
    question=data.get("question","").strip()
    profile=data.get("profile",{})
    if not question:return jsonify({"error":"Question is required"}),400
    context=json.dumps(profile,ensure_ascii=False)
    answer=ai(f"User profile: {context}\nUser question: {question}",
      """You are SAHAYAK AI, a helpful Government Life Manager for India.
Explain government paperwork, schemes and next steps in simple language.
Do not claim that a person is officially eligible. Say 'possible match' and advise checking official criteria.
Keep answers concise, practical, and structured. Never invent government links or deadlines.""")
    if not answer:
        q=question.lower()
        if "scheme" in q: answer="Open the Scheme Eligibility Engine, complete your profile, and review the possible matches with their official portals."
        elif "document" in q or "certificate" in q: answer="Upload the document in OCR + ReCorrect Engine, review extracted fields, correct them, then save your profile."
        else: answer="I can help you organise documents, check possible scheme matches, explain forms, and create reminders. Tell me what you need to do."
    return jsonify({"answer":answer})

@app.post("/api/ocr")
def ocr():
    if "file" not in request.files:return jsonify({"error":"Upload a file"}),400
    f=request.files["file"]
    if not f.filename:return jsonify({"error":"No file selected"}),400
    content=f.read()
    text=""
    provider="fallback"
    if vision_client:
        try:
            image=vision.Image(content=content)
            response=vision_client.document_text_detection(image=image)
            if response.error.message: raise Exception(response.error.message)
            text=response.full_text_annotation.text or ""
            provider="google-cloud-vision"
        except Exception as e:
            return jsonify({"error":f"OCR service error: {str(e)}"}),500
    if not text:
        return jsonify({"error":"Google Vision is not configured. Add GOOGLE_APPLICATION_CREDENTIALS to use server OCR.","setup_required":True}),503
    return jsonify({"text":text,"fields":extract_fields(text),"provider":provider})

@app.post("/api/recorrect")
def recorrect():
    data=request.get_json() or {}
    fields=data.get("fields",{})
    missing=[k for k in ["name","age","category","income","state","district"] if not str(fields.get(k,"")).strip()]
    issues=[]
    try:
        age=int(fields.get("age") or 0)
        if age and not 1<=age<=120:issues.append("Age looks unusual.")
    except: issues.append("Age must be a number.")
    try:
        income=float(str(fields.get("income","")).replace(",","") or 0)
        if income<0:issues.append("Income cannot be negative.")
    except: issues.append("Income must be numeric.")
    score=max(0,100-len(missing)*12-len(issues)*8)
    suggestion=ai(json.dumps(fields),
      """You are a document data quality assistant. Return concise plain text with only:
1) missing or suspicious fields,
2) what the user should verify.
Never fabricate document values.""")
    return jsonify({"score":score,"missing":missing,"issues":issues,"suggestion":suggestion or "Review highlighted or missing fields before saving."})

@app.post("/api/eligibility")
def eligibility():
    p=request.get_json() or {}
    try: age=int(p.get("age") or 0)
    except: age=0
    try: income=float(str(p.get("income") or 0).replace(",",""))
    except: income=0
    category=str(p.get("category","")).upper()
    education=p.get("education","")
    matches=[]
    if category in ["SC","ST","OBC"] and income<=250000 and education in ["School Student","College Student"]:
        matches.append({"name":"Post-Matric Scholarship","status":"Possible match","reason":"Your category, income and education match this prototype rule.","documents":["Income certificate","Category certificate","Marksheet"],"official":"https://scholarships.gov.in/"})
    if category in ["EWS","GENERAL"] and income<=800000 and education in ["School Student","College Student"]:
        matches.append({"name":"Education Support Search","status":"Possible match","reason":"Your profile matches this prototype income/category rule. Verify the current scheme criteria.","documents":["Income certificate","Identity proof","Education documents"],"official":"https://scholarships.gov.in/"})
    if age>=18 and p.get("state") and p.get("district"):
        matches.append({"name":"Skill Development Search","status":"Possible match","reason":"Your age and location meet this prototype discovery rule.","documents":["Identity proof","Address proof"],"official":"https://www.skillindia.gov.in/"})
    return jsonify({"matches":matches,"disclaimer":"Prototype rules are for hackathon demonstration. Always verify current eligibility and requirements on the official portal."})

@app.get("/api/profile/<user_id>")
def get_profile(user_id):
    return jsonify(read_json(PROFILE_FILE,{}).get(user_id,{}))

@app.put("/api/profile/<user_id>")
def save_profile(user_id):
    data=request.get_json() or {}
    allp=read_json(PROFILE_FILE,{})
    data["updated_at"]=datetime.utcnow().isoformat()+"Z"
    allp[user_id]=data; write_json(PROFILE_FILE,allp)
    return jsonify({"ok":True,"profile":data})

@app.post("/api/reminders/<user_id>")
def add_reminder(user_id):
    data=request.get_json() or {}
    if not data.get("task") or not data.get("date"):return jsonify({"error":"Task and date are required"}),400
    allr=read_json(REMINDER_FILE,{})
    item={"id":str(uuid.uuid4()),"task":data["task"],"date":data["date"],"done":False}
    allr.setdefault(user_id,[]).append(item);write_json(REMINDER_FILE,allr)
    return jsonify(item)

@app.get("/api/reminders/<user_id>")
def reminders(user_id):return jsonify(read_json(REMINDER_FILE,{}).get(user_id,[]))

if __name__=="__main__":
    app.run(debug=True,port=5000)
