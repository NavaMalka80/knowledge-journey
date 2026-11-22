# 🖥️ הרצה מקומית: מדריך צעד אחר צעד

איך מריצים את הפרויקט על המחשב שלך, ואיך רואים את בדיקת קובץ המשחק בפעולה.
בכל שלב פותחים טרמינל: ב-Windows זה **PowerShell**, וב-Mac זה **Terminal**.

## שלב 1: לוודא שיש uv

```bash
uv --version
```

אם מופיע מספר גרסה, אפשר לדלג לשלב 2. אם מופיעה שגיאה, מתקינים את uv.

ב-Windows:

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

ב-Mac:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

אחרי ההתקנה סוגרים את הטרמינל ופותחים חדש, כדי שהפקודה `uv` תוכר.

## שלב 2: להביא את הקוד

**אם הפרויקט עוד לא נמצא אצלך במחשב:**

```bash
git clone https://github.com/NavaMalka80/knowledge-journey.git
```

```bash
cd knowledge-journey
```

**אם הפרויקט כבר אצלך:** נכנסים לתיקייה שלו ומושכים את העדכונים:

```bash
git fetch origin
```

## שלב 3: לבחור ענף

אם ה-Pull Request של שלב 1 כבר מוזג, עובדים על `main`:

```bash
git checkout main
```

```bash
git pull
```

אם הוא עוד לא מוזג, הקוד נמצא בענף של השלב:

```bash
git checkout claude/stoic-hawking-1r4se6
```

## שלב 4: להתקין את התלויות

```bash
uv sync
```

הפקודה יוצרת את התיקייה `.venv` ומתקינה את Pydantic ואת שאר הכלים, בגרסאות המדויקות מתוך `uv.lock`.

## שלב 5: לבדוק את המשחק לדוגמה

```bash
uv run kj validate examples/water-cycle.json
```

התוצאה הצפויה:

```text
✓ examples/water-cycle.json: המשחק 'מסע הידע: מחזור המים' תקין (17 שאלות)
```

## שלב 6: ניסוי, לשבור משהו בכוונה

1. פותחים את `examples/water-cycle.json` בעורך (למשל VS Code).
2. מחפשים את השורה `"כולם נבלעים באדמה",` ומוחקים אותה כולה.
3. שומרים ומריצים שוב:

```bash
uv run kj validate examples/water-cycle.json
```

התוצאה הצפויה:

```text
✗ examples/water-cycle.json: נמצאו 1 בעיות
  • anchor_question.answers: צריכים להיות לפחות 4 פריטים, ויש 3
```

ההודעה אומרת **איפה** הבעיה (התשובות של שאלת העוגן) ו**מה** הבעיה: לכל שאלה צריכות להיות ארבע תשובות.

**עוד ניסויים**, אחד בכל פעם:

| מה משנים | מה זה מראה |
|---|---|
| מוחקים `"rationale"` בשאלה כלשהי | הנימוק הוא חובה |
| משנים `"duration_minutes": 8` ל-`10` | משך התחנה קבוע בתבנית |
| משנים `"rationale"` ל-`"rationel"` | שגיאת כתיב בשם של שדה נתפסת |

## שלב 7: להחזיר את הקובץ למצבו המקורי

```bash
git restore examples/water-cycle.json
```

git זוכר את הגרסה השמורה של הקובץ, והפקודה מבטלת את כל השינויים שעשית בו.

## שלב 8: להריץ את כל הבדיקות האוטומטיות

```bash
uv run pytest
```

בסוף אמורה להופיע השורה `passed`, עם טבלת כיסוי. אלה אותן בדיקות שה-CI מריץ ב-GitHub.

---

אם משהו לא עובד, מעתיקים את מה שמופיע בטרמינל לשיחה עם Claude Code, ומבינים יחד מה קרה.
