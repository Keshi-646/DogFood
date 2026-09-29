import csv, io, sqlite3, tomllib
from functools import wraps
from flask import Flask, jsonify, request, session, render_template, abort, Response
from .db import get_db, init_db, seed_db

def create_app(config_path=".dogfood.toml"):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)
    app.config["DATABASE_URL"] = "data/hackforge.db"
    app.config["SECRET_KEY"] = "change-me"
    app.config["HOST"] = cfg["portal"]["host"]
    app.config["PORT"] = cfg["portal"]["port"]
    app.config["DATABASE_URL"] = "data/hackforge.db"
    import os
    app.config["DATABASE_URL"] = os.environ.get("DATABASE_URL", app.config["DATABASE_URL"])
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", app.config["SECRET_KEY"])

    @app.before_request
    def ensure_db():
        init_db()

    def current_user():
        uid = session.get("user_id")
        if not uid: return None
        return get_db().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()

    def role_required(*roles):
        def deco(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                u = current_user()
                if not u or u["role"] not in roles:
                    return jsonify(error="forbidden"), 403
                return fn(*args, **kwargs)
            return wrapper
        return deco

    @app.get("/")
    def index():
        db=get_db()
        event=db.execute("SELECT * FROM events LIMIT 1").fetchone()
        submissions=db.execute("""SELECT s.*,t.name team_name FROM submissions s
                                  JOIN teams t ON t.id=s.team_id ORDER BY s.id DESC""").fetchall()
        return render_template("index.html", event=event, submissions=submissions, user=current_user())

    @app.post("/api/login")
    def login():
        data=request.get_json() or {}
        u=get_db().execute("SELECT * FROM users WHERE email=? AND password=?",
                           (data.get("email"),data.get("password"))).fetchone()
        if not u: return jsonify(error="invalid credentials"),401
        session["user_id"]=u["id"]
        return jsonify(id=u["id"],name=u["name"],role=u["role"])

    @app.post("/api/logout")
    def logout():
        session.clear()
        return jsonify(ok=True)

    @app.post("/api/register")
    def register():
        data=request.get_json() or {}
        required=("name","email","password")
        if not all(data.get(k) for k in required):
            return jsonify(error="name, email and password are required"),400
        db=get_db()
        try:
            uid=db.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,'participant')",
                           (data["name"],data["email"],data["password"])).lastrowid
            db.commit()
        except sqlite3.IntegrityError:
            return jsonify(error="email already exists"),409
        return jsonify(id=uid),201

    @app.post("/api/teams")
    @role_required("participant","organizer","admin")
    def create_team():
        data=request.get_json() or {}; u=current_user()
        db=get_db()
        event=db.execute("SELECT id FROM events LIMIT 1").fetchone()
        tid=db.execute("INSERT INTO teams(event_id,name,captain_id) VALUES(?,?,?)",
                       (event["id"],data["name"],u["id"])).lastrowid
        db.execute("INSERT INTO team_members(team_id,user_id) VALUES(?,?)",(tid,u["id"]))
        db.commit()
        return jsonify(id=tid),201

    @app.post("/api/submissions")
    @role_required("participant","organizer","admin")
    def create_submission():
        d=request.get_json() or {}; db=get_db()
        team=db.execute("SELECT * FROM teams WHERE id=?",(d.get("team_id"),)).fetchone()
        if not team: return jsonify(error="team not found"),404
        u=current_user()
        if u["role"]=="participant":
            member=db.execute("SELECT 1 FROM team_members WHERE team_id=? AND user_id=?",
                              (team["id"],u["id"])).fetchone()
            if not member: return jsonify(error="not a team member"),403
        sid=db.execute("""INSERT INTO submissions(event_id,team_id,title,description,repo_url,demo_url)
                          VALUES(?,?,?,?,?,?)""",
                       (team["event_id"],team["id"],d["title"],d["description"],
                        d.get("repo_url"),d.get("demo_url"))).lastrowid
        db.commit()
        return jsonify(id=sid),201

    @app.post("/api/assignments")
    @role_required("organizer","admin")
    def assign():
        d=request.get_json() or {}; db=get_db()
        try:
            aid=db.execute("INSERT INTO assignments(submission_id,judge_id) VALUES(?,?)",
                           (d["submission_id"],d["judge_id"])).lastrowid
            db.commit()
        except sqlite3.IntegrityError:
            return jsonify(error="assignment already exists"),409
        return jsonify(id=aid),201

    @app.get("/api/judge/assignments")
    @role_required("judge")
    def judge_assignments():
        u=current_user(); db=get_db()
        rows=db.execute("""SELECT a.id assignment_id,s.id submission_id,s.title,t.name team_name
                          FROM assignments a JOIN submissions s ON s.id=a.submission_id
                          JOIN teams t ON t.id=s.team_id WHERE a.judge_id=?""",(u["id"],)).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.get("/api/judge/scores/<int:submission_id>")
    @role_required("judge","organizer","admin")
    def judge_scores(submission_id):
        u=current_user(); db=get_db()
        if u["role"]=="judge":
            ok=db.execute("SELECT 1 FROM assignments WHERE submission_id=? AND judge_id=?",
                          (submission_id,u["id"])).fetchone()
            if not ok: return jsonify(error="score access denied"),403
        rows=db.execute("""SELECT sc.id,sc.criterion_id,rc.name,sc.score
                           FROM scores sc JOIN assignments a ON a.id=sc.assignment_id
                           JOIN rubric_criteria rc ON rc.id=sc.criterion_id
                           WHERE a.submission_id=?""",(submission_id,)).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.post("/api/judge/score")
    @role_required("judge")
    def score():
        d=request.get_json() or {}; u=current_user(); db=get_db()
        a=db.execute("SELECT * FROM assignments WHERE id=? AND judge_id=?",
                     (d["assignment_id"],u["id"])).fetchone()
        if not a: return jsonify(error="assignment not owned by current judge"),403
        c=db.execute("SELECT * FROM rubric_criteria WHERE id=?",(d["criterion_id"],)).fetchone()
        if not c: return jsonify(error="criterion not found"),404
        score=float(d["score"])
        if score<0 or score>100: return jsonify(error="score must be 0..100"),400
        db.execute("""INSERT INTO scores(assignment_id,criterion_id,score) VALUES(?,?,?)
                      ON CONFLICT(assignment_id,criterion_id) DO UPDATE SET score=excluded.score""",
                   (a["id"],c["id"],score))
        db.commit()
        return jsonify(ok=True)

    @app.post("/api/normalize")
    @role_required("organizer","admin")
    def normalize():
        db=get_db()
        subs=db.execute("SELECT id FROM submissions").fetchall()
        raw={}
        for s in subs:
            rows=db.execute("""SELECT a.judge_id,rc.weight,sc.score
                               FROM scores sc JOIN assignments a ON a.id=sc.assignment_id
                               JOIN rubric_criteria rc ON rc.id=sc.criterion_id
                               WHERE a.submission_id=?""",(s["id"],)).fetchall()
            by_judge={}
            for r in rows:
                by_judge.setdefault(r["judge_id"],0)
                by_judge[r["judge_id"]] += r["score"]*r["weight"]/100.0
            raw[s["id"]] = sum(by_judge.values())/len(by_judge) if by_judge else 0
        vals=list(raw.values())
        lo,hi=(min(vals),max(vals)) if vals else (0,0)
        for sid,val in raw.items():
            normalized=100.0 if hi==lo and hi>0 else (0 if hi==lo else (val-lo)/(hi-lo)*100)
            db.execute("""INSERT INTO normalized_results(submission_id,raw_score,normalized_score)
                          VALUES(?,?,?) ON CONFLICT(submission_id) DO UPDATE SET
                          raw_score=excluded.raw_score,normalized_score=excluded.normalized_score""",
                       (sid,val,normalized))
        ranked=db.execute("SELECT submission_id FROM normalized_results ORDER BY normalized_score DESC").fetchall()
        for i,r in enumerate(ranked,1):
            db.execute("UPDATE normalized_results SET rank=? WHERE submission_id=?",(i,r["submission_id"]))
        db.commit()
        return jsonify(ok=True)

    @app.get("/api/results")
    def results():
        db=get_db()
        rows=db.execute("""SELECT s.id,s.title,t.name team_name,n.raw_score,n.normalized_score,n.rank
                           FROM normalized_results n JOIN submissions s ON s.id=n.submission_id
                           JOIN teams t ON t.id=s.team_id ORDER BY n.rank""").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.get("/api/gallery")
    def gallery():
        db=get_db()
        rows=db.execute("""SELECT s.id,s.title,s.description,s.repo_url,s.demo_url,t.name team_name
                           FROM submissions s JOIN teams t ON t.id=s.team_id
                           WHERE s.status='submitted' ORDER BY s.id DESC""").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.get("/api/export/submissions.csv")
    @role_required("organizer","admin")
    def export_csv():
        db=get_db()
        rows=db.execute("""SELECT s.id,s.title,t.name team_name,s.repo_url,s.demo_url,s.status
                           FROM submissions s JOIN teams t ON t.id=s.team_id ORDER BY s.id""").fetchall()
        out=io.StringIO(); w=csv.writer(out)
        w.writerow(["id","title","team","repo_url","demo_url","status"])
        for r in rows: w.writerow(list(r))
        return Response(out.getvalue(),mimetype="text/csv",
                        headers={"Content-Disposition":"attachment; filename=submissions.csv"})

    @app.cli.command("seed")
    def seed():
        init_db(); seed_db(); print("Seeded.")

    return app
