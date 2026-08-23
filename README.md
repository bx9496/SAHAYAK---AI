# 🇮🇳 SAHAYAK AI

### Your Personal Government Life Admin

SAHAYAK AI is a GovTech platform designed to simplify government paperwork, scheme discovery, document processing, and citizen support through AI-powered assistance.

Built for **HACQUIRE 2026** under:

**Problem Statement PS-10: Paperwork & Access**  
**Domain: GovTech / Inclusion**

---

## 🎯 Problem Statement

Government forms, schemes, claims, and documents are often difficult to understand and navigate due to:

- Complex paperwork
- Eligibility confusion
- Language barriers
- Missing documentation
- Lack of guidance
- Missed deadlines

SAHAYAK AI provides a single platform that helps citizens understand, process, and access government services more easily.

---

## 🚀 Core Features

### 🤖 AI Government Life Manager
An AI-powered assistant that helps users:

- Understand government procedures
- Get document guidance
- Receive personalized recommendations
- Manage reminders and important tasks
- Access citizen support information

---

### 🎯 Scheme Eligibility Engine
Users can enter their:

- Age
- Category
- Income
- Education
- State
- District

The system evaluates potential scheme eligibility and recommends relevant government benefits.

---

### 📄 OCR + ReCorrect Engine

Upload documents and automatically:

- Extract text using OCR
- Detect important information
- Correct extracted data
- Save document history
- Translate content

### 🌐 Multilingual Support

Supported languages:

- English
- Hindi
- Odia

Document text can be translated between all supported languages.

---

### 🚨 Emergency Contact & Medical Support

Users can securely store:

- Emergency contact details
- Relationship information
- Phone numbers
- Essential medical information

---

## 🔐 Login & KYC

SAHAYAK AI includes:

- User Registration
- Secure Login
- Session Management
- KYC Metadata Storage
- User Profile Management

Login is required before accessing platform services.

---

## 💾 Database Features

The platform stores:

- User Accounts
- User Profiles
- KYC Metadata
- OCR Scan History
- Translated Documents
- Emergency Contacts
- Reminders

SQLite is used for the hackathon prototype.

---

## 🏗️ System Architecture

```text
Login & KYC
      │
      ▼
SAHAYAK Dashboard
      │
 ┌────┼────┐
 │    │    │
 ▼    ▼    ▼
AI  OCR  Eligibility
Mgr Engine Engine
 │    │    │
 └────┼────┘
      ▼
   Database
