# Freshco Bakers — Digital Management Platform

Monorepo: **Flutter** (web/Android/iOS/desktop, with a 3D-styled UI) + **FastAPI** backend + **PostgreSQL** (single central database, per the SRS).

```
freshco-bakers/
├── backend/         # FastAPI app, models, migrations
├── frontend/        # Flutter app (customer site, admin, POS)
├── docs/            # Original SRS/architecture document
│   └── progress/    # Module tracking log (one file per pushed module)
└── README.md
```

**3D UI note:** the app doesn't use a 3D engine/model assets — depth is done with real Flutter
perspective transforms (`Matrix4` + `rotateX/rotateY`) in `shared/widgets/tilt_3d_card.dart`.
Product cards and the hero button tilt in 3D as you drag/hover over them, with dynamic shadows
that shift with the tilt. This keeps it lightweight and works on web, mobile and desktop.

Status: **Module 1 — Project Scaffolding + Freshco Bakers branding + 3D UI** ✅
See `docs/progress/` for the full module log.

---

## 1. Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                # then edit .env with your real DATABASE_URL, SECRET_KEY

uvicorn app.main:app --reload       # runs at http://localhost:8000
```

Check it's alive:
- http://localhost:8000/  → Interactive Developer Hub (or JSON for API clients)
- http://localhost:8000/dashboard  → Visual Operations & Test Console
- http://localhost:8000/scalar  → Modern Scalar API Reference
- http://localhost:8000/docs  → Custom-themed Swagger UI
- http://localhost:8000/api/v1/health  → Health probe
- http://localhost:8000/api/v1/health/db  (needs Postgres running & DATABASE_URL correct)

Local PostgreSQL database matching `DATABASE_URL`:

```bash
createdb freshco_bakers_db
```

### Migrations (Alembic)
Once the first models land (next module):

```bash
alembic revision --autogenerate -m "create initial tables"
alembic upgrade head
```

---

## 2. Frontend setup

You need the Flutter SDK installed locally. This scaffolding was created without running
`flutter create`, so platform folders (`android/`, `ios/`, `web/`...) don't exist yet.

```bash
cd frontend
flutter create . --project-name freshco_bakers --org com.freshcobakers
flutter pub get
flutter run -d chrome                     # or: flutter run  (for a connected device)
```

Point the app at your backend:

```bash
flutter run --dart-define=API_BASE_URL=http://localhost:8000/api/v1
```

You should see the **Freshco Bakers** hero screen with a tilting "Order Now" button and
4 tilt-able featured product cards.

---

## 3. Push to GitHub

From the `freshco-bakers/` root:

```bash
git init
git add .
git commit -m "Module 1: Freshco Bakers scaffolding + 3D UI"

git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

For every future module:

```bash
git add .
git commit -m "Module X: <short description>"
git push
```

---

## 4. Module tracking

After every push, a new file is added to `docs/progress/` named `module-XX-<name>.md`,
recording: what was built, exact files added/changed, and the commit message used.
This is your running changelog — check `docs/progress/` any time to see what's done
and what's next.
