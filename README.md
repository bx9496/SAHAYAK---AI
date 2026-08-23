# 🇮🇳 SAHAYAK AI

### Your Personal Government Life Admin

SAHAYAK AI is a GovTech platform designed to simplify government paperwork, documents, schemes, and essential services for users who find government processes difficult to understand or navigate.

Built for **HACQUIRE 2026 – PS-10: Paperwork & Access**.

---

## 🎯 Problem Statement

Government schemes, documents, forms, and claims can be difficult to navigate because of complex procedures, unclear eligibility criteria, paperwork, language barriers, and missed deadlines.

SAHAYAK AI brings these processes together into one simple and accessible platform.

---

## 💡 Our Solution

SAHAYAK AI follows a simple flow:

**Login → Scan → Understand → Check Eligibility → Save → Take Action**

The platform combines AI assistance, OCR, document correction, eligibility checking, multilingual support, and personal reminders.

---

## 🚀 Core Features

### 1. 🤖 AI Government Life Manager

A personalized AI assistant that helps users:

- Understand government procedures
- Understand documents
- Get guidance on government services
- Identify next steps
- Manage important reminders

---

### 2. 🎯 Scheme Eligibility Engine

Users enter their personal information and the system checks possible scheme matches using predefined eligibility rules.

It considers information such as:

- Age
- Category
- Annual income
- Education
- State
- District

The system also shows commonly required documents and directs users toward official portals.

> Eligibility results are prototype matches and must be verified through the official government portal.

---

### 3. 📄 OCR + ReCorrect Engine

Users can upload document images and extract information using OCR.

The system allows users to:

- Scan documents
- Extract text
- Review extracted information
- Correct errors
- Check data quality
- Save verified information
- Save OCR scan history

### 🌐 Multilingual OCR

Supported document languages:

- English
- Hindi
- Odia

Extracted text can also be translated between:

**English ↔ Hindi ↔ Odia**

---

## 🔐 Login & KYC

Users create an account before accessing the platform.

The system provides:

- User registration
- Login
- Session authentication
- KYC information
- Masked document numbers
- Personal user profile

---

## 💾 Data Storage

SAHAYAK AI uses a database to store user-specific information.

Stored data includes:

- User accounts
- KYC metadata
- User profiles
- OCR scan history
- Translated document text
- Reminders
- Emergency contact information

---

## 🚨 Emergency Contact & Medical Support

Users can save:

- Emergency contact
- Relationship
- Phone number
- Optional essential medical information

This information is accessible through the AI Government Life Manager.

---

## 🌗 Accessibility

SAHAYAK AI supports:

- Light Mode
- Dark Mode
- Simple user interface
- Multilingual document processing

---

## 🏗️ System Architecture

```text
                    SAHAYAK AI
                         │
                  🔐 Login + KYC
                         │
                   👤 User Profile
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   🤖 AI Manager    📄 OCR Engine    🎯 Eligibility
        │                │                │
        │          ReCorrect +          │
        │          Translation           │
        │                │                │
        └────────────────┼────────────────┘
                         │
                   💾 Database
                         │
              🔔 Reminders + Support
