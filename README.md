# 🏫 E-DBA: Lightweight Education Data Bay Area

A project shared by the courses **Software Engineering** and **Advanced Software Development Workshop**.

> This system is designed to support secure, structured, and policy-compliant data exchange among higher education institutions.

---

## 📌 Project Overview

**E-DBA** is a lightweight educational data platform inspired by the **International Data Space (IDS)** model. It enables secure data sharing, identity verification, and service access across registered universities and institutions.

Main objectives:
- Easy and secure data provision & consumption
- Student identity authentication
- Thesis access and download services
- Course information sharing
- Online payment system
- Optional data vault service

---

## 👥 User Roles

| Role             | Description                                                                 |
|------------------|-----------------------------------------------------------------------------|
| `T-Admin`        | System-level admin for user help and admin setup                           |
| `E-Admin`        | Approves organization registrations, manages policies, sets membership fees |
| `Senior E-Admin` | Final approval of registrations                                             |
| `O-Convener`     | Represents an institution, manages services, members, and payments         |
| `User`           | Can be data provider/consumer with tiered access rights                    |

---

## 🔐 Access Rights

| Access Level | Role                             |
|--------------|----------------------------------|
| 1            | Public data access               |
| 2            | Private data consumption         |
| 3            | Private data provision           |

Users with higher-level access inherit all lower-level permissions.

---

## 🛠️ System Features

### 1. Workspace for Each Organization
- Bank account setup
- Member management
- Service configuration (e.g., authentication, thesis sharing)

### 2. Services
- **Course Information Sharing** (Free & Public)
- **Thesis Sharing**
- **Student Identity Authentication**
- **Student GPA Record Access**
- **Online Payment** (Transfer, Alipay, PayPal, WeChat, etc.)
- **Vault (Optional)** – Data storage for organizations without a maintained database

### 3. Payment System
- Organization-initiated transfers
- Service fees set by O-Convener
- Membership fee configuration by E-Admin

---

## 💳 Charges Summary

| Service Type                       | Charge                      |
|-----------------------------------|-----------------------------|
| Course Info Sharing               | Free                        |
| Membership (Level 1)              | 1000 RMB total or 10 RMB/user |
| Membership (Level 2)              | 100 RMB/user                |
| Membership (Level 3)              | Free                        |
| Thesis/Authentication services    | Custom (set by O-Convener) |

---

## 📂 External Interfaces

> ⚠️ **Note**: Some API-related functions (e.g., student record retrieval, bank account verification) require **BNBU local intranet (局域网)** access. Please ensure the system is deployed within the BNBU environment to access these services.

External interfaces include:

- **Student Info DB**: For identity & GPA
- **Thesis DB**: Search by keyword or title
- **Banking Interface**: Validate accounts, transfer money

All interfaces are configured in the system by the data provider and **not hard-coded** into the source code.

---

## 🚀 Deployment

> _Deployment instructions to be added later._

The system is designed to run on a Linux server with:
- Stable disk storage (SATA)
- TCP/IP network protocol
- XML-based data messaging format
- Lightweight performance-oriented OS and environment

Database compatibility: **MySQL, Oracle, SQL Server, Sybase, DB2**  
Supports **timestamp-based** and **non-intrusive log-based** data synchronization.

---

## 📄 License

To be determined.

---

## 🤝 Contributors

This project is developed as part of university coursework.

---

## 📬 Contact

For questions, please contact the project maintainers or course instructors.

---

## 👥 Contributors

| Avatar | Name | GitHub | Role |
|--------|------|--------|------|
| <img src="https://avatars.githubusercontent.com/ZhaozixiOwO" width="50"/> | Zixi Zhao | [@ZhaozixiOwO](https://github.com/ZhaozixiOwO) | Project Creator / Developer |
| <img src="https://avatars.githubusercontent.com/FuShiNanSheng" width="50"/> | FuShiNanSheng | [@FuShiNanSheng](https://github.com/FuShiNanSheng) | Developer / Collaborator |

