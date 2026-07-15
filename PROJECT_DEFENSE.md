# 🛡️ Aris 4.0 — Project Defense Document

---

## Table of Contents
1. [Problem Understanding](#1-problem-understanding)
2. [Technical Work — Diagrams](#2-technical-work--diagrams)
3. [Tools and Technologies](#3-tools-and-technologies)
4. [System Demonstration](#4-system-demonstration)
5. [Presentation & Reflection](#5-presentation--reflection)

---

## 1. Problem Understanding

### 1.1 The Problem Statement

Traditional educational platforms face several critical challenges in the modern learning environment:

| Challenge | Impact |
|-----------|--------|
| **Disconnected learning experiences** | Students, instructors, and parents operate in silos with no unified platform |
| **Low student engagement** | Lack of gamification and competitive elements leads to poor motivation |
| **No progress visibility** | Instructors and parents cannot easily track student performance over time |
| **Limited access to resources** | Educational materials are scattered across different systems |
| **Offline reliability concerns** | Cloud-only platforms fail when internet connectivity is unreliable |

**Aris 4.0** was built to address these pain points by providing a **unified, gamified educational platform** that connects all stakeholders in the learning ecosystem.

### 1.2 How Aris 4.0 Solves These Problems

| Problem | Aris 4.0 Solution |
|---------|-------------------|
| **Disconnected stakeholders** | Four distinct user roles (Student, Instructor, Admin, Parent) each with tailored dashboards |
| **Low engagement** | XP-based gamification with 5-tier ranking system, leaderboards, and challenges |
| **No progress visibility** | Real-time quiz submissions, student performance reports, and parent-child progress tracking |
| **Scattered resources** | Centralized digital library & archive repository for all class materials |
| **Data resilience** | Outbox Pattern with django-q2 syncs local SQLite to Supabase PostgreSQL — the app keeps working even if the cloud DB is temporarily unreachable |

---

## 2. Technical Work — Diagrams

### 2.1 Use Case Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ARIS 4.0 SYSTEM                                     │
│                                                                                  │
│  ┌──────────┐                                                                    │
│  │  STUDENT │                                                                   │
│  └────┬─────┘                                                                    │
│       │                                                                          │
│       ├──► Register / Login                                                      │
│       ├──► Enroll in Academic Classes                                            │
│       ├──► Access Class Modules & Content                                        │
│       ├──► Take Quizzes (multi-choice)                                           │
│       ├──► View Quiz Results & Scores                                            │
│       ├──► Earn XP & Level Up (5 Tiers)                                          │
│       ├──► View Leaderboard Rankings                                             │
│       ├──► Participate in Challenges                                             │
│       ├──► Browse Digital Library & Downloads                                    │
│       ├──► View Archive Repository                                               │
│       └──► Edit Student Profile (bio, avatar, quote)                             │
│                                                                                  │
│  ┌──────────────┐                                                                │
│  │  INSTRUCTOR   │                                                               │
│  └──────┬───────┘                                                                │
│         │                                                                        │
│         ├──► Apply for Approval (Admin reviews)                                  │
│         ├──► Create & Manage Academic Classes                                    │
│         ├──► Organize Content into Modules                                       │
│         ├──► Upload Class Materials (files, docs)                                │
│         ├──► Create Quizzes with Questions & Choices                             │
│         ├──► Grade & Review Quiz Submissions                                     │
│         ├──► View Student Performance Reports                                    │
│         ├──► Browse Student Directory per Class                                  │
│         ├──► Upload Books to Digital Library                                     │
│         └──► Edit Instructor Profile (bio, focus areas, manuscripts)             │
│                                                                                  │
│  ┌──────────┐                                                                    │
│  │  ADMIN   │                                                                   │
│  └────┬─────┘                                                                    │
│       │                                                                          │
│       ├──► Approve / Disapprove Instructor Applications                          │
│       ├──► Delete Instructor Requests                                            │
│       ├──► Create & Manage Challenges (with XP prize pools)                      │
│       ├──► Award XP to Challenge Winners                                         │
│       ├──► Reset ALL Student XP (season reset)                                   │
│       └──► Monitor Instructor Progress                                           │
│                                                                                  │
│  ┌──────────┐                                                                    │
│  │  PARENT  │                                                                   │
│  └────┬─────┘                                                                    │
│       │                                                                          │
│       ├──► Register via Invite Link Code                                         │
│       ├──► Link to Child Account (PRNT-XXXXXX code)                              │
│       ├──► View Child's Class Enrollment                                         │
│       ├──► View Child's Quiz Results                                             │
│       ├──► Track Child's XP Progress & Tier                                      │
│       └──► Monitor Child's Academic Performance                                  │
│                                                                                  │
│  ┌──────────────┐                                                                │
│  │  BACKGROUND  │  (Automated — no user interaction)                             │
│  │  SYNC SYSTEM │                                                                │
│  └──────┬───────┘                                                                │
│         │                                                                        │
│         ├──► Detect Local Database Changes (via Django Signals)                  │
│         ├──► Queue SyncRecords (Outbox Pattern)                                  │
│         ├──► Check Supabase Connectivity                                         │
│         ├──► Push Pending Records to Cloud PostgreSQL                            │
│         ├──► Upload Media Files to Supabase Storage                              │
│         ├──► Handle Retry on Failure                                             │
│         └──► Ensure Remote Schema Consistency                                    │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Explanation of Use Case Coverage:**

The diagram covers the **four primary actors** of the system plus the **automated background sync system**. Every major functional area is represented:

- **Authentication & Authorization**: All users register/login; instructors require admin approval
- **Content Management**: Instructors create structured courses (Classes → Modules → Content)
- **Assessment**: Quiz creation, taking, auto-grading, and result display
- **Gamification**: XP system, tier progression, leaderboards, challenges with prize pools
- **Resource Management**: Digital library, archive repository, file uploads/downloads
- **Parental Monitoring**: Parent-child linking, progress tracking
| **Data Resilience**: Local SQLite + background sync to Supabase PostgreSQL ensures no data loss on cloud outage

---

### 2.2 Entity Relationship Diagram (ERD)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      ARIS 4.0 — DATABASE SCHEMA                                │
└──────────────────────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────────────────────────┐
                              │              User (AbstractUser)     │
                              │  ┌─────────────────────────────────┐ │
                              │  │ PK  id         : INTEGER        │ │
                              │  │     username   : VARCHAR(150)   │ │
                              │  │     email      : VARCHAR(254)   │ │
                              │  │     password   : VARCHAR(128)   │ │
                              │  │     role       : VARCHAR(20)    │ │  ← student|instructor|admin|parent
                              │  │     is_approved: BOOLEAN        │ │  ← instructor gate
                              │  │     xp         : INTEGER        │ │  ← gamification core
                              │  └────────┬────────┬──────┬────────┘ │
                              └───────────┼────────┼──────┼──────────┘
                                          │        │      │
              ┌───────────────────────────┘        │      └──────────────────────────────┐
              ▼                                    ▼                                     ▼
┌──────────────────────────┐          ┌──────────────────────────┐          ┌──────────────────────────┐
│    InstructorProfile     │          │     StudentProfile       │          │    ParentChildLink       │
│ ┌──────────────────────┐ │          │ ┌──────────────────────┐ │          │ ┌──────────────────────┐ │
│ │ PK id      : INTEGER │ │          │ │ PK id      : INTEGER │ │          │ │ PK id      : INTEGER │ │
│ │ FK user_id : INTEGER │◄┤ 1:1      │ │ FK user_id : INTEGER │◄┤ 1:1      │ │ FK parent_id: INTEGER│◄┤ N:1→User
│ │    title_role:VARCHAR│ │          │ │    avatar   : IMAGE  │ │          │ │ FK child_id: INTEGER │◄┤ N:1→User
│ │    bio      : TEXT   │ │          │ │    bio      : TEXT   │ │          │ │    link_code:VARCHAR │ │
│ │    avatar   : IMAGE  │ │          │ │    inspire  :VARCHAR │ │          │ │    relationship:VARCHAR│
│ │    established: INT  │ │          │ │    quote    :VARCHAR │ │          │ │    is_active:BOOLEAN │ │
│ │    academic_focus:JSON│ │         │ └──────────────────────┘ │          │ └──────────────────────┘ │
│ │    methodologies:JSON │ │         └──────────────────────────┘          └──────────────────────────┘
│ │    manuscripts :JSON  │ │
│ └──────────────────────┘ │
└──────────────────────────┘

         │
         │ 1:N (taught_classes)
         ▼
┌──────────────────────────┐          ┌──────────────────────────┐
│     AcademicClass        │          │      Challenge           │
│ ┌──────────────────────┐ │          │ ┌──────────────────────┐ │
│ │ PK id      : INTEGER │ │          │ │ PK id      : INTEGER │ │
│ │    code     :VARCHAR │ │          │ │    title    :VARCHAR │ │
│ │    title    :VARCHAR │ │          │ │    description:TEXT  │ │
│ │    schedule :VARCHAR │ │          │ │    rules    : TEXT   │ │
│ │    meeting_link:VARCHAR│         │ │ FK created_by:INTEGER│◄┤ N:1→User (Admin)
│ │    slug     : SLUG   │ │          │ │    start_date:DATETIME│ │
│ │ FK instructor:INTEGER│◄┤ N:1→User │ │    end_date :DATETIME│ │
│ └──┬────────┬──────────┘ │          │ │    is_active:BOOLEAN │ │
│    │        │            │          │ │    prize_pool_xp:INT │ │
│    │        │ M:N        │          │ └─────────┬────────────┘ │
│    │        ▼  (students)│          │           │              │
│    │  ┌──────────────┐   │          │           │ M:N          │
│    │  │ User (Student)│  │          │           ▼              │
│    │  └──────────────┘   │          │  ┌──────────────────────┐ │
│    │                     │          │  │   ChallengeClass      │ │
│    │ 1:N                 │          │  │ ┌──────────────────────┐ │
│    ▼                     │          │  │ │ PK id      : INTEGER │ │
│ ┌──────────────────────┐ │          │  │ │ FK challenge:INTEGER │◄┤
│ │      Module          │ │          │  │ │ FK academic_class:INT│◄┤
│ │ ┌──────────────────┐ │ │          │  │ └──────────────────────┘ │
│ │ │ PK id   : INTEGER │ │ │          │  └──────────────────────────┘
│ │ │    title : VARCHAR │ │ │          │
│ │ │    order : INTEGER │ │ │          │
│ │ │ FK academic_class │◄┤ N:1       │
│ │ └──┬────────────────┘ │ │          │
│ │    │ 1:N              │ │          │
│ │    ▼                  │ │          │
│ │ ┌──────────────────────┐ │         │
│ │ │   ClassContent       │ │         │
│ │ │ ┌──────────────────┐ │ │         │
│ │ │ │ PK id   : INTEGER │ │ │        │
│ │ │ │    title : VARCHAR│ │ │        │
│ │ │ │    desc  : TEXT   │ │ │        │
│ │ │ │    file  : FILE   │ │ │        │
│ │ │ │    order : INTEGER│ │ │        │
│ │ │ │ FK academic_class │◄┤ N:1     │
│ │ │ │ FK module : INTEGER│◄┤ N:1     │
│ │ │ └──────────────────┘ │ │        │
│ │ └──────────────────────┘ │        │
│ │                          │        │
│ │ 1:N                      │        │
│ ▼                          │        │
│ ┌──────────────────────┐   │        │
│ │       Quiz           │   │        │
│ │ ┌──────────────────┐ │   │        │
│ │ │ PK id   : INTEGER │ │   │        │
│ │ │    title : VARCHAR │ │   │        │
│ │ │    desc  : TEXT    │ │   │        │
│ │ │ FK creator:INTEGER │◄──┤ N:1→User│
│ │ │ FK academic_class  │◄──┤ N:1    │
│ │ │ FK module: INTEGER │◄──┤ N:1    │
│ │ └──┬─────────────────┘   │        │
│ │    │ 1:N                 │        │
│ │    ▼                     │        │
│ │ ┌──────────────────────┐ │        │
│ │ │     Question         │ │        │
│ │ │ ┌──────────────────┐ │ │        │
│ │ │ │ PK id   : INTEGER │ │ │       │
│ │ │ │    text  : TEXT   │ │ │       │
│ │ │ │    order : INTEGER│ │ │       │
│ │ │ │ FK quiz : INTEGER │◄┤ N:1    │
│ │ │ └──┬────────────────┘ │        │
│ │ │    │ 1:N              │        │
│ │ │    ▼                  │        │
│ │ │ ┌──────────────────────┐ │      │
│ │ │ │      Choice          │ │      │
│ │ │ │ ┌──────────────────┐ │ │      │
│ │ │ │ │ PK id   : INTEGER │ │ │     │
│ │ │ │ │    text  : VARCHAR│ │ │     │
│ │ │ │ │    is_correct:BOOL│ │ │     │
│ │ │ │ │    order : INTEGER│ │ │     │
│ │ │ │ │ FK question:INTEGER│◄┤ N:1  │
│ │ │ │ └──────────────────┘ │ │      │
│ │ │ └──────────────────────┘ │      │
│ │ └──────────────────────────┘      │
│ │                                   │
│ │          ┌──────────────────────────┐
│ │          │  StudentQuizSubmission   │
│ │          │ ┌──────────────────────┐ │
│ │          │ │ PK id      : INTEGER │ │
│ │          │ │    score    : INTEGER│ │  ← auto-calculated
│ │          │ │    total    : INTEGER│ │
│ │          │ │    answers  : JSON   │ │  ← {question_id: choice_id}
│ │          │ │    submitted_at:DATETIME│
│ │          │ │ FK student  : INTEGER│◄┤ N:1→User
│ │          │ │ FK quiz     : INTEGER│◄┤ N:1→Quiz
│ │          │ └──────────────────────┘ │
│ │          └──────────────────────────┘
│ │
│ └──────────────────────────────────────┘

┌──────────────────────────┐          ┌──────────────────────────┐
│    ArchiveCategory       │          │      LibraryBook         │
│ ┌──────────────────────┐ │          │ ┌──────────────────────┐ │
│ │ PK id   : INTEGER    │ │          │ │ PK id      : INTEGER │ │
│ │    name  : VARCHAR    │ │          │ │    title    : VARCHAR│ │
│ │    slug  : SLUG       │ │          │ │    description:TEXT │ │
│ └──┬────────────────────┘ │          │ │    file     : FILE   │ │
│    │ 1:N                  │          │ │    thumbnail: IMAGE  │ │
│    ▼                      │          │ │ FK uploaded_by:INTEGER│◄┤ N:1→User (Instructor)
│ ┌──────────────────────────┐         │ │ FK academic_class:INT│◄┤ N:1→AcademicClass
│ │     ArchiveItem          │         │ └──────────────────────┘ │
│ │ ┌──────────────────────┐ │         └──────────────────────────┘
│ │ │ PK id       : INTEGER│ │
│ │ │    title     : VARCHAR│ │        ┌──────────────────────────┐
│ │ │    subtitle  : VARCHAR│ │        │      SyncRecord          │
│ │ │    description: TEXT  │ │        │  (Outbox Pattern)        │
│ │ │    layout_variant:VARCHAR│      │ ┌──────────────────────┐ │
│ │ │    status_label:VARCHAR│       │ │ PK id      : INTEGER │ │
│ │ │    timestamp  : VARCHAR│ │       │ │    table_name:VARCHAR│ │  ← which model table
│ │ │    is_italic  : BOOL  │ │        │ │    row_id   : BIGINT │ │  ← PK of the local row
│ │ │    is_featured: BOOL  │ │        │ │    action   : VARCHAR│ │  ← create|update|delete
│ │ │    has_certificate:BOOL│ │       │ │    status   : VARCHAR│ │  ← pending|synced|failed
│ │ │    certificate_url:URL│ │        │ │    payload_json:JSON │ │  ← serialized row data
│ │ │    has_actions : BOOL │ │        │ │    file_paths : JSON  │ │  ← media files to upload
│ │ │    download_url: URL  │ │        │ │    retry_count: INT   │ │
│ │ │    cover_image : IMAGE│ │        │ │    error_message:TEXT │ │
│ │ │ FK category   : INTEGER│◄┤ N:1  │ │    created_at:DATETIME│ │
│ │ └──────────────────────┘ │        │ │    synced_at :DATETIME│ │
│ └──────────────────────────┘        │ └──────────────────────┘ │
                                       └──────────────────────────┘
```

**Key Relationships Explained:**

| Relationship | Type | Purpose |
|-------------|------|---------|
| **User → AcademicClass** | 1:N (instructor) + M:N (students) | Instructors teach classes; students enroll in them |
| **AcademicClass → Module → ClassContent** | 1:N → 1:N | Hierarchical course structure |
| **AcademicClass → Quiz → Question → Choice** | 1:N → 1:N → 1:N | Assessment chain |
| **User → StudentQuizSubmission ← Quiz** | N:1 both ways | Tracks which student took which quiz |
| **User → InstructorProfile / StudentProfile** | 1:1 | Extended profile data per role |
| **User → ParentChildLink ← User** | Self-referential N:N | Parent-child account linking |
| **Admin User → Challenge ← AcademicClass** | M:N via ChallengeClass | Challenges assigned to specific classes |
| **SyncRecord** | Standalone outbox table | Decouples local writes from cloud sync |

---

## 3. Tools and Technologies

### 3.1 Technology Stack Overview

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Backend Framework** | Django | 6.0.5 | Full-stack web framework — handles routing, ORM, auth, templates |
| **Language** | Python | 3.x | Primary programming language |
| **Local Database** | SQLite | 3.x | Local/offline data store (file-based, zero-config) |
| **Cloud Database** | Supabase (PostgreSQL) | Latest | Remote sync target; full relational cloud DB |
| **Cloud Storage** | Supabase Storage | Latest | Media file hosting (avatars, library books, class content) |
| **Background Tasks** | django-q2 | 1.10.0 | Asynchronous task queue for sync operations |
| **Frontend CSS** | Tailwind CSS | 4.x | Utility-first CSS framework for responsive UI |
| **CSS Processing** | pytailwindcss | 0.3.0 | Python-native Tailwind build tool |
| **Containerization** | Docker + Docker Compose | Latest | Multi-service deployment (web, qcluster, ngrok) |
| **Public Tunneling** | ngrok | Latest | Expose local server to the internet via HTTPS |
| **Environment Config** | python-decouple | 3.8 | Secure environment variable management |
| **HTTP Client** | requests | 2.34.2 | HTTP requests to Supabase REST API |
| **Supabase SDK** | supabase-py + realtime-py | 2.31.0 | Supabase client libraries |
| **Image Processing** | Pillow | 12.2.0 | Image field handling in Django |
| **Templating** | Jinja2 | 3.1.6 | Django's template engine (bundled) |

### 3.2 How Each Tool Was Applied

#### Django 6.0.5 — The Backbone
- Custom `AbstractUser` model extended with `role`, `is_approved`, and `xp` fields
- Django ORM manages all 15+ models with relationships, migrations, and queries
- Class-based and function-based views handle all HTTP request/response logic
- Django's built-in authentication system (login, logout, password reset)
- Django Templates with template inheritance (`base.html` extended by all pages)
- Django Signals trigger `SyncRecord` creation on every database write

> **Important note on architecture:** Aris 4.0 is a **traditional server-rendered web application** — users access it entirely through a browser via the ngrok HTTPS URL. The local SQLite database and background sync are **server-side infrastructure** (the Django server writes to local SQLite, and django-q2 asynchronously pushes that data to Supabase PostgreSQL). This is not an offline-first user experience; it is a **backend data resilience pattern** that prevents data loss if the Supabase cloud service is temporarily unreachable.

#### Supabase — Cloud Sync Layer
- **PostgreSQL**: Remote database mirroring local SQLite tables
- **Storage**: Hosts uploaded media files (avatars, library books, class materials)
- **REST API**: Programmatic access for sync operations
- **Row Level Security (RLS)**: Service-role key bypasses RLS for server-side sync

#### django-q2 — Background Task Queue
- Scheduled cron job runs `sync_pending_records()` every 60 seconds
- Processes pending `SyncRecord` entries in batches
- Handles retries with exponential backoff on failure
- Non-blocking — users never wait for cloud sync

#### Docker & Docker Compose
- **`web` service**: Django development server on port 8000
- **`qcluster` service**: django-q2 background worker
- **`ngrok` service** (optional profile): Public HTTPS tunnel
- Volume mounts for SQLite database and media files persistence

#### Tailwind CSS
- Utility classes for responsive, mobile-first design
- Custom animations (fadeInUp, float, pulseSoft, countUp)
- Neubrutalist design aesthetic with box shadows and bold typography
- Font pairings: Playfair Display (headings) + Space Mono (UI) + Inter (body)

---

## 4. System Demonstration

### 4.1 Functionality → Use Case Mapping

| Use Case | Implementation | URL / Page |
|----------|---------------|------------|
| **User Registration** | `RegisterForm` with role selection (Student/Instructor); `ParentRegisterForm` via invite code | `/register/`, `/parent/register/` |
| **User Login** | `LoginForm` using Django's `AuthenticationForm`; role-based redirect to appropriate dashboard | `/login/` |
| **Instructor Approval** | Admin reviews pending instructors; toggles `is_approved` flag | `/admin-dashboard/` |
| **Class Enrollment** | Students browse available classes via `select_level_view`; enroll with one click | `/select-level/` |
| **Course Content** | Instructors create Modules → ClassContent with file uploads; students view structured content | `/study/class/<slug>/` |
| **Quiz Taking** | Multi-choice quiz with auto-grading; answers stored as JSON; score calculated server-side | `/quiz/<id>/take/` |
| **Quiz Results** | Detailed per-question review showing correct vs. selected answers; XP awarded on completion | `/quiz/<id>/result/` |
| **XP & Tiers** | 5-tier system: Initiate (0) → Scholar (500) → Alpha Vanguard (1500) → Elite Scholar (3000) → Grandmaster (5000+) | All student pages show XP progress |
| **Leaderboard** | Top 5 students ranked by XP; current user's rank highlighted; XP gap to #1 displayed | `/challenge/<id>/leaderboard/` |
| **Challenges** | Admin creates time-bound challenges with XP prize pools; assigns to specific classes; awards winners | `/admin-dashboard/challenge/create/` |
| **Digital Library** | Instructors upload books with thumbnails; students browse and download | `/archive/library/` |
| **Archive Repository** | Magazine-style layout with categories; items show certificates and actions | `/archive/` |
| **Parent Dashboard** | Parents link to children via PRNT-XXXXXX code; view child's classes, quizzes, XP | `/parent/dashboard/` |
| **Instructor Profiles** | Rich profiles with bio, academic focus areas, methodologies, manuscripts, avatar | `/teacher-profile/<username>/` |
| **Student Profiles** | Profiles with avatar, bio, inspirational message, favorite quote | `/student-profile/<username>/` |
| **Backend Data Sync** | Outbox Pattern: every DB write creates a SyncRecord; django-q2 pushes local SQLite → Supabase PostgreSQL | Background (server-side, automated) |

### 4.2 Key Pages & User Interface

| Page | Purpose | Key UI Elements |
|------|---------|----------------|
| **Landing Page** (`/`) | Public homepage | Hero section with animated text, role-based CTA buttons, student/instructor stats |
| **Student Dashboard** (`/study/`) | Central hub for students | Enrolled classes grid, XP progress bar with tier badge, quick links |
| **Instructor Dashboard** | Central hub for instructors | Class management cards, quick-create quiz button, student performance overview |
| **Admin Dashboard** | Admin control panel | Pending instructor approvals table, challenge management, XP reset button |
| **Class Detail** | Course content view | Module accordion, content list with file downloads, quiz links |
| **Quiz Interface** | Quiz-taking page | Question card with radio choices, progress indicator, submit button |
| **Quiz Result** | Post-quiz results | Score display, per-question correct/incorrect breakdown, XP earned notification |
| **Leaderboard** | Competitive rankings | Top 5 ranked cards with tier badges, current user's rank highlight, XP gap indicator |
| **Library** | Digital book repository | Book cards with thumbnails, download buttons, upload form (instructor) |
| **Archive** | Achievement showcase | Magazine-style cards with certificates, timestamps, featured items |

### 4.3 Design & Usability Highlights

- **Neubrutalist Aesthetic**: Bold borders, hard box-shadows, high contrast — distinctive visual identity
- **Responsive Design**: Tailwind breakpoints ensure usability on mobile, tablet, and desktop
- **Animation System**: Custom CSS keyframe animations (fadeInUp, float, countUp) with `prefers-reduced-motion` support
- **Role-Based Navigation**: Dynamic navbar adapts to user role; relevant links only
- **Security**: Django CSRF protection, trusted origins for ngrok, service-role key never exposed to frontend

---

## 5. Presentation & Reflection

### 5.1 Communication Flow

The defense presentation should follow this logical flow:

1. **Introduction** (1 min): What is Aris 4.0? The problem it solves.
2. **Live Demo** (3-4 min): Walk through the key use cases as different roles
   - Register as a student → log in → browse classes → take a quiz → see XP gained
   - Switch to instructor → create a class → add a module → upload content → create a quiz
   - Switch to admin → approve instructor → create challenge → award XP
   - Show parent dashboard with linked child
3. **Technical Deep-Dive** (2 min): ERD walkthrough, sync architecture (Outbox Pattern)
4. **Reflection** (1 min): Lessons learned, challenges, future improvements
5. **Q&A** (remaining time)

### 5.2 Lessons Learned

| Lesson | Detail |
|--------|--------|
| **Backend data sync requires careful design** | The Outbox Pattern with django-q2 provided reliable sync between local SQLite and cloud PostgreSQL. The key insight: this is server-side infrastructure, not a user-facing offline feature — users always access the app via the web through ngrok |
| **Django's signals are powerful but need care** | Signals fire on every model save — had to ensure sync triggers don't create infinite loops |
| **Tailwind CSS reduces CSS debt** | Utility classes eliminated the need for separate stylesheets; the entire project uses one small custom CSS block per template |
| **Role-based routing requires discipline** | With 4 user roles, keeping views and templates organized required strict URL naming conventions |
| **Docker Compose simplifies multi-service coordination** | Running web + qcluster + ngrok as separate services made development and deployment seamless |
| **Supabase is an excellent Django companion** | PostgreSQL + Storage + REST API provides everything needed for cloud sync without managing infrastructure |

### 5.3 Challenges Faced

| Challenge | How It Was Overcome |
|-----------|---------------------|
| **Sync payload serialization** | Built a robust `build_payload()` function that handles all Django field types (FileField → URL, DateTime → ISO string, JSON → dict) |
| **File uploads to Supabase Storage** | Created `file_uploader.py` module that uploads media files and stores the returned public URL in the synced row |
| **Connectivity detection** | Implemented lightweight REST health-check with Django cache TTL to avoid hammering Supabase on every cron tick |
| **Schema drift between local SQLite and remote PostgreSQL** | Added `ensure_remote_schema()` that validates table structure before sync |
| **Admin approval workflow** | Extended User model with `is_approved` boolean; instructors see a "pending approval" page until approved |
| **XP calculation consistency** | Centralized tier logic in `tiers.py` shared by views, context processors, and templates |

### 5.4 Suggestions for Future Improvement

1. **Real-time Features**: Integrate Supabase Realtime for live leaderboard updates and instant notifications
2. **Advanced Quiz Types**: Support for essay questions, file upload submissions, and peer review
3. **AI-Powered Features**: Auto-generate quiz questions from uploaded content; intelligent study recommendations
4. **Mobile App**: Package as PWA (Progressive Web App) for offline mobile access
5. **Analytics Dashboard**: Advanced learning analytics for instructors and admins
6. **Internationalization (i18n)**: Multi-language support for broader accessibility
7. **SSO Integration**: OAuth login with Google, Microsoft, or institutional accounts
8. **Automated Testing**: Comprehensive test suite with pytest for all views, models, and sync operations

---

## Appendix: Quick Reference

### Project Structure
```
project001/
├── accounts/              # Main Django app (models, views, forms, templates, tiers)
├── sync_manager/          # Background data sync module (Outbox Pattern — local SQLite → Supabase PostgreSQL)
│   └── sync/
│       ├── tasks.py       # django-q2 sync tasks
│       ├── connectivity.py # Online/offline detection
│       ├── file_uploader.py # Supabase Storage uploads
│       └── remote_schema.py # Schema validation
├── ONLportal/             # Django project settings
│   ├── settings.py
│   ├── supabase_client.py # Supabase SDK initialization
│   └── urls.py
├── Dockerfile
├── docker-compose.yml     # 3 services: web, qcluster, ngrok
├── requirements.txt       # Python dependencies
└── manage.py
```

### Key URLs
| URL Pattern | View | Access |
|-------------|------|--------|
| `/` | `home_view` | Public |
| `/register/` | `register_view` | Public |
| `/login/` | `login_view` | Public |
| `/study/` | `student_dashboard_view` | Student |
| `/instructor-dashboard/` | `instructor_dashboard_view` | Instructor |
| `/admin-dashboard/` | `admin_dashboard_view` | Admin |
| `/archive/` | `archive_view` | All authenticated |
| `/archive/library/` | `library_view` | All authenticated |
