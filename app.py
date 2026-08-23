import os,re,uuid,sqlite3,hashlib,secrets,json
from datetime import datetime
from functools import wraps
from flask import Flask,render_template,request,jsonify,session,redirect,url_for  # type: ignore[reportMissingImports]
try:
  from importlib import import_module
  load_dotenv=import_module('dotenv').load_dotenv
except (ImportError,AttributeError):
  def load_dotenv(*args, **kwargs):
    return False
try:
  from openai import OpenAI  # type: ignore[reportMissingImports]
except ImportError:
  OpenAI=None
load_dotenv()
app=Flask(__name__);app.secret_key=os.getenv('FLASK_SECRET_KEY','change-this-secret');app.config['MAX_CONTENT_LENGTH']=10*1024*1024
DB=os.getenv('DATABASE_FILE','sahayak.db');KEY=os.getenv('OPENAI_API_KEY','');MODEL=os.getenv('OPENAI_MODEL','gpt-5');client=OpenAI(api_key=KEY) if KEY and OpenAI else None

def db():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def init_db():
 c=db();c.executescript('''CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT UNIQUE,password_hash TEXT,created_at TEXT);CREATE TABLE IF NOT EXISTS kyc(id TEXT PRIMARY KEY,user_id TEXT,name TEXT,phone TEXT,document_type TEXT,masked_document TEXT,status TEXT,created_at TEXT);CREATE TABLE IF NOT EXISTS profiles(user_id TEXT PRIMARY KEY,data TEXT,updated_at TEXT);CREATE TABLE IF NOT EXISTS reminders(id TEXT PRIMARY KEY,user_id TEXT,task TEXT,date TEXT,done INTEGER DEFAULT 0);CREATE TABLE IF NOT EXISTS scans(id TEXT PRIMARY KEY,user_id TEXT,filename TEXT,source_language TEXT,extracted_text TEXT NOT NULL,translated_text TEXT,target_language TEXT,created_at TEXT);CREATE TABLE IF NOT EXISTS emergency_contacts(id TEXT PRIMARY KEY,user_id TEXT,name TEXT,relation TEXT,phone TEXT,medical_info TEXT,created_at TEXT);''');c.commit();c.close()
def hp(p):
 s=secrets.token_hex(16);return s+'$'+hashlib.pbkdf2_hmac('sha256',p.encode(),s.encode(),120000).hex()
def vp(p,h):
 try:s,d=h.split('$',1);return secrets.compare_digest(hashlib.pbkdf2_hmac('sha256',p.encode(),s.encode(),120000).hex(),d)
 except:return False
def uid():return session.get('user_id')
def auth(f):
 @wraps(f)
 def w(*a,**k):return f(*a,**k) if uid() else (jsonify(error='Login required'),401)
 return w
def mask(x):x=str(x).strip();return '••••' if len(x)<=4 else '•'*(len(x)-4)+x[-4:]
def ai(p,i):
 if not client:return None
 try:return client.responses.create(model=MODEL,instructions=i,input=p).output_text
 except:return None
def fields(text):
 def pick(r):
  m=re.search(r,text,re.I);return m.group(1).strip() if m else ''
 cat=re.search(r'\b(SC|ST|OBC|EWS|GENERAL)\b',text,re.I)
 inc=pick(r'(?:annual\s*)?income\s*[:\-]?\s*(?:rs\.?|₹)?\s*([\d,]{3,})')
 return {'name':pick(r'(?:name|applicant name)\s*[:\-]?\s*([A-Za-z][A-Za-z .\'-]{2,60})'),'guardian':pick(r'(?:father|mother|guardian)(?:\'s)?\s*name?\s*[:\-]?\s*([A-Za-z][A-Za-z .\'-]{2,60})'),'age':pick(r'\bage\s*[:\-]?\s*(\d{1,3})'),'category':cat.group(1).upper() if cat else '','income':inc.replace(',',''),'state':pick(r'\bstate\s*[:\-]?\s*([A-Za-z ]{3,50})'),'district':pick(r'\bdistrict\s*[:\-]?\s*([A-Za-z ]{3,50})'),'education':''}
@app.get('/')
def home():
 if not uid(): return redirect(url_for('account'))
 return render_template('index.html')
@app.get('/ai-manager')
@auth
def ai_page():return render_template('ai-manager.html')
@app.get('/eligibility')
@auth
def el_page():return render_template('eligibility.html')
@app.get('/document-engine')
@auth
def doc_page():return render_template('document-engine.html')
@app.get('/account')
def account():return render_template('account.html')
@app.get('/api/health')
def health():return jsonify(status='ok',backend='running',ai_mode='openai' if client else 'demo',database='sqlite')
@app.post('/api/register')
def register():
 d=request.get_json() or {};e=str(d.get('email','')).strip().lower();p=str(d.get('password',''))
 if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$',e):return jsonify(error='Enter a valid email.'),400
 if len(p)<6:return jsonify(error='Password must be at least 6 characters.'),400
 u='usr_'+uuid.uuid4().hex[:12];c=db()
 try:c.execute('INSERT INTO users VALUES(?,?,?,?)',(u,e,hp(p),datetime.utcnow().isoformat()+'Z'));c.commit()
 except sqlite3.IntegrityError:c.close();return jsonify(error='Account already exists.'),409
 c.close();session['user_id']=u;return jsonify(ok=True,user={'id':u,'email':e}),201
@app.post('/api/login')
def login():
 d=request.get_json() or {};e=str(d.get('email','')).strip().lower();p=str(d.get('password',''));c=db();r=c.execute('SELECT * FROM users WHERE email=?',(e,)).fetchone();c.close()
 if not r or not vp(p,r['password_hash']):return jsonify(error='Invalid email or password.'),401
 session['user_id']=r['id'];return jsonify(ok=True,user={'id':r['id'],'email':r['email']})
@app.post('/api/logout')
def logout():session.clear();return jsonify(ok=True)
@app.get('/api/me')
def me():
 if not uid():return jsonify(authenticated=False)
 c=db();u=c.execute('SELECT id,email,created_at FROM users WHERE id=?',(uid(),)).fetchone();k=c.execute('SELECT id,name,phone,document_type,masked_document,status,created_at FROM kyc WHERE user_id=? ORDER BY created_at DESC LIMIT 1',(uid(),)).fetchone();c.close();return jsonify(authenticated=True,user=dict(u) if u else None,kyc=dict(k) if k else None)
@app.post('/api/kyc')
@auth
def kyc():
 d=request.get_json() or {};n=str(d.get('name','')).strip();ph=re.sub(r'[\s\-()]','',str(d.get('phone','')));dt=str(d.get('documentType','')).lower();dn=str(d.get('documentNumber','')).strip();allowed={'government_id','national_id','passport','tax_id','driving_license','voter_id'}
 if len(n)<2:return jsonify(error='Valid name is required.'),400
 if not re.fullmatch(r'\+?[0-9]{7,15}',ph):return jsonify(error='Valid phone is required.'),400
 if dt not in allowed:return jsonify(error='Unsupported document type.'),400
 if not 4<=len(dn)<=50:return jsonify(error='Document number must be 4-50 characters.'),400
 kid='KYC-'+uuid.uuid4().hex[:10].upper();now=datetime.utcnow().isoformat()+'Z';c=db();c.execute('DELETE FROM kyc WHERE user_id=?',(uid(),));c.execute('INSERT INTO kyc VALUES(?,?,?,?,?,?,?,?)',(kid,uid(),n,ph,dt,mask(dn),'VERIFIED',now));c.commit();c.close();return jsonify(success=True,verificationId=kid,status='VERIFIED',name=n,documentType=dt,maskedDocumentNumber=mask(dn)),201
@app.get('/api/profile')
@auth
def profile():
 c=db();r=c.execute('SELECT data FROM profiles WHERE user_id=?',(uid(),)).fetchone();c.close();return jsonify(json.loads(r['data']) if r else {})
@app.put('/api/profile')
@auth
def save_profile():
 d=request.get_json() or {};d.pop('documentNumber',None);now=datetime.utcnow().isoformat()+'Z';c=db();c.execute('INSERT INTO profiles VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET data=excluded.data,updated_at=excluded.updated_at',(uid(),json.dumps(d,ensure_ascii=False),now));c.commit();c.close();return jsonify(ok=True,profile=d)
@app.post('/api/chat')
@auth
def chat():
 d=request.get_json() or {};q=str(d.get('question','')).strip();c=db();r=c.execute('SELECT data FROM profiles WHERE user_id=?',(uid(),)).fetchone();c.close();p=json.loads(r['data']) if r else {}
 a=ai(f'Profile:{json.dumps(p)}\nQuestion:{q}','You are SAHAYAK AI, a concise Government Life Manager for India. Never claim official eligibility or invent links/deadlines. Explain next steps simply.')
 if not a:a='Open Scheme Eligibility for possible matches, OCR + ReCorrect to save profile information, or Account for KYC. Always verify official government requirements.'
 return jsonify(answer=a)
@app.post('/api/recorrect')
@auth
def recorrect():
 f=(request.get_json() or {}).get('fields',{});req=['name','age','category','income','state','district'];missing=[k for k in req if not str(f.get(k,'')).strip()];issues=[]
 try:
  age=int(f.get('age') or 0)
  if age and not 1<=age<=120:issues.append('Age looks unusual.')
 except:issues.append('Age must be numeric.')
 try:
  inc=float(str(f.get('income','')).replace(',','') or 0)
  if inc<0:issues.append('Income cannot be negative.')
 except:issues.append('Income must be numeric.')
 score=max(0,100-len(missing)*12-len(issues)*8);s=ai(json.dumps(f),'Identify only missing or suspicious fields and what to verify. Never fabricate values.') or 'Review missing or suspicious fields before saving.';return jsonify(score=score,missing=missing,issues=issues,suggestion=s)
@app.post('/api/eligibility')
@auth
def eligibility():
 p=request.get_json() or {};age=int(p.get('age') or 0) if str(p.get('age','')).isdigit() else 0
 try:inc=float(str(p.get('income') or 0).replace(',',''))
 except:inc=0
 cat=str(p.get('category','')).upper();edu=p.get('education','');m=[]
 if cat in ['SC','ST','OBC'] and inc<=250000 and edu in ['School Student','College Student']:m.append({'name':'Post-Matric Scholarship','status':'Possible match','reason':'Prototype rule matches category, income and education.','documents':['Income certificate','Category certificate','Marksheet'],'official':'https://scholarships.gov.in/'})
 if cat in ['EWS','GENERAL'] and inc<=800000 and edu in ['School Student','College Student']:m.append({'name':'Education Support Search','status':'Possible match','reason':'Prototype income/category rule match.','documents':['Income certificate','Identity proof','Education documents'],'official':'https://scholarships.gov.in/'})
 if age>=18 and p.get('state') and p.get('district'):m.append({'name':'Skill Development Search','status':'Possible match','reason':'Prototype discovery rule matches age and location.','documents':['Identity proof','Address proof'],'official':'https://www.skillindia.gov.in/'})
 return jsonify(matches=m,disclaimer='Prototype rules only. Verify current eligibility on the official portal.')
@app.post('/api/reminders')
@auth
def add_reminder():
 d=request.get_json() or {};t=str(d.get('task','')).strip();date=str(d.get('date','')).strip()
 if not t or not date:return jsonify(error='Task and date are required.'),400
 i=uuid.uuid4().hex;c=db();c.execute('INSERT INTO reminders VALUES(?,?,?,?,0)',(i,uid(),t,date));c.commit();c.close();return jsonify(id=i,task=t,date=date,done=False),201
@app.get('/api/reminders')
@auth
def reminders():
 c=db();r=c.execute('SELECT id,task,date,done FROM reminders WHERE user_id=? ORDER BY date',(uid(),)).fetchall();c.close();return jsonify([dict(x) for x in r])
@app.delete('/api/reminders/<rid>')
@auth
def del_reminder(rid):
 c=db();c.execute('DELETE FROM reminders WHERE id=? AND user_id=?',(rid,uid()));c.commit();c.close();return jsonify(ok=True)
@app.post("/api/scans")
@auth
def save_scan():
    data=request.get_json() or {}; text=str(data.get("extractedText","")).strip()
    if not text: return jsonify({"error":"No OCR text to save."}),400
    sid="scan_"+uuid.uuid4().hex[:12]; now=datetime.utcnow().isoformat()+"Z"
    conn=db(); conn.execute("""INSERT INTO scans(id,user_id,filename,source_language,extracted_text,translated_text,target_language,created_at)
      VALUES(?,?,?,?,?,?,?,?)""",(sid,uid(),str(data.get("filename","")),str(data.get("sourceLanguage","eng")),text,str(data.get("translatedText","")),str(data.get("targetLanguage","English")),now))
    conn.commit(); conn.close(); return jsonify({"ok":True,"scanId":sid,"createdAt":now})

@app.get("/api/scans")
@auth
def list_scans():
    conn=db(); rows=conn.execute("""SELECT id,filename,source_language,extracted_text,translated_text,target_language,created_at
      FROM scans WHERE user_id=? ORDER BY created_at DESC LIMIT 20""",(uid(),)).fetchall(); conn.close()
    return jsonify([dict(r) for r in rows])

@app.post("/api/translate")
@auth
def translate_text():
    data=request.get_json() or {}; text=str(data.get("text","")).strip(); target=str(data.get("target","English")).strip()
    if not text: return jsonify({"error":"Text is required."}),400
    if target not in {"English","Hindi","Odia"}: return jsonify({"error":"Choose English, Hindi or Odia."}),400
    result=ai(f"Translate the following document text to {target}. Preserve names, numbers, dates, IDs, addresses and formatting exactly where possible. Do not add information.\n\n{text}",
      f"""You are a document translation engine. Translate to {target}. Return only the translation. Preserve personal data exactly and never invent facts.""")
    return jsonify({"translation":result or text,"target":target,"mode":"openai" if result else "demo-fallback"})

@app.post("/api/emergency")
@auth
def save_emergency():
    data=request.get_json() or {}; name=str(data.get("name","")).strip(); relation=str(data.get("relation","")).strip()
    phone=re.sub(r"[\s\-()]","",str(data.get("phone","")).strip()); medical=str(data.get("medicalInfo","")).strip()
    if len(name)<2: return jsonify({"error":"Contact name is required."}),400
    if not re.fullmatch(r"\+?[0-9]{7,15}",phone): return jsonify({"error":"Enter a valid phone number."}),400
    eid="em_"+uuid.uuid4().hex[:12]; now=datetime.utcnow().isoformat()+"Z"
    conn=db(); conn.execute("DELETE FROM emergency_contacts WHERE user_id=?",(uid(),))
    conn.execute("INSERT INTO emergency_contacts VALUES(?,?,?,?,?,?,?)",(eid,uid(),name,relation,phone,medical,now))
    conn.commit(); conn.close(); return jsonify({"ok":True,"id":eid})

@app.get("/api/emergency")
@auth
def get_emergency():
    conn=db(); row=conn.execute("""SELECT id,name,relation,phone,medical_info,created_at
      FROM emergency_contacts WHERE user_id=? LIMIT 1""",(uid(),)).fetchone(); conn.close()
    return jsonify(dict(row) if row else {})

init_db()
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.getenv('PORT',5000)),debug=False)
