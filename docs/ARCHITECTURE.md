# 🏗️ ארכיטקטורה

## תמונה כללית

```mermaid
flowchart TB
    subgraph Teacher["מחשב המורה (מקוון)"]
        Studio["סטודיו ההכנה<br/>אתר סטטי · GitHub Pages"]
        Project[("קובץ פרויקט<br/>+ מדיה מקומית")]
        Studio <--> Project
    end

    subgraph Cloud["ענן (מכסה חינמית)"]
        Proxy["שרת מתווך<br/>FastAPI · stateless"]
    end

    Anthropic["Claude API<br/>סוכן בקרת הידע"]

    subgraph Classroom["מחשב הכיתה (ללא אינטרנט)"]
        Screen["מסך מרכזי"]
        Panel["לוח מנחה"]
        Clickers["קליקרים / הזנה ידנית"]
        Panel <-- BroadcastChannel --> Screen
        Clickers --> Panel
    end

    Studio -- "HTTPS: תוכן + קוד גישה" --> Proxy
    Proxy -- "HTTPS: בקשה + API key" --> Anthropic
    Anthropic -- "משוב JSON" --> Proxy
    Proxy -- "משוב JSON" --> Studio
    Studio -- "הורדה: ZIP + דף הנחיה" --> Classroom
```

## רכיבים

| רכיב | אחריות | טכנולוגיה | שומר מידע? |
|---|---|---|---|
| **מודל הנתונים** | הגדרה אחת של "משחק", ולידציה וייצוא JSON Schema | Python · Pydantic | לא |
| **סטודיו ההכנה** | כרטיס זהות, תבנית, מדיה, משוב, אישור וייצוא | HTML/CSS/JS | רק בדפדפן ובקובץ של המורה |
| **שרת מתווך** | מחזיק את מפתח ה-API, אוכף קוד גישה והגבלת קצב, מריץ את לוגיקת הסוכן | Python · FastAPI | **לא** (stateless) |
| **סוכן בקרת הידע** | בדיקה פדגוגית לפי מחוון, החזרת משוב מובנה | Claude API · Structured Outputs | לא |
| **נגן המשחק** | הפעלה בכיתה: מסך, לוח מנחה, הצבעות, ניקוד ודוח | HTML/CSS/JS ללא תלויות | תוצאות במחשב הכיתה בלבד |

## זרימת עבודה של מורה

```mermaid
sequenceDiagram
    actor T as מורה
    participant S as סטודיו
    participant P as שרת מתווך
    participant C as Claude API
    T->>S: ממלאת כרטיס זהות ותוכן
    T->>S: "שלחי לבקרה"
    S->>P: תוכן + קוד גישה
    P->>C: מחוון + כרטיס זהות + תוכן
    C-->>P: משוב מובנה (JSON)
    P-->>S: משוב
    S-->>T: הערות ליד כל שדה
    T->>S: מתקנת, או מבקשת "הצע תיקון"
    T->>S: מאשרת
    S-->>T: הורדה: game.zip + guide.pdf + project file
```

## מקור אמת אחד למבנה המשחק

המבנה מוגדר **פעם אחת** ב-Python (Pydantic) ומיוצא ל-**JSON Schema**.
- השרת משתמש במודלים ישירות.
- הסטודיו והנגן (JavaScript) מוודאים מול ה-Schema.
- כך אין "שתי גרסאות" של אותה הגדרה שעלולות להתפצל.

## אילוצים מרכזיים

| אילוץ | השלכה |
|---|---|
| הכיתה עלולה להיות בלי אינטרנט | הנגן סטטי לגמרי, בלי CDN, ועובד מ-`file://` |
| אין תקציב לאחסון | אין שמירת חומרים בשרת. הסטודיו סטטי ב-GitHub Pages |
| מפתח API עולה כסף | המפתח רק בשרת המתווך, עם קוד גישה, הגבלת קצב ותקרת הוצאה |
| דגם הקליקרים טרם נבדק | שכבת מתאמים (Adapter): ידני ומקלדת קודם, ציוד אמיתי בהמשך |
| פרטיות תלמידות | אין זיהוי אישי. הדוחות קבוצתיים |

## רשומות החלטה (ADR)

- [0001: משחק אופליין ללא שמירת חומרים בשרת](adr/0001-offline-first-no-server-storage.md)
- [0002: שרת מתווך להגנה על מפתח ה-API](adr/0002-api-key-proxy.md)
- [0003: הסוכן מבקר, הוא לא כותב](adr/0003-ai-reviews-not-authors.md)
