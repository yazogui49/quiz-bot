-- ============================================================
-- Bulk-import questions from a JSON file
--
-- HOW TO USE — Supabase SQL Editor (recommended)
-- 1. Open your Supabase project → SQL Editor
-- 2. Replace the JSON array below with your full questions file
-- 3. Run it
--
-- HOW TO USE — psql CLI
--   export DB_URL="postgresql://postgres:<password>@<host>:5432/postgres"
--   psql "$DB_URL" -f 02_import_questions.sql
--
-- ── Expected JSON shape ──────────────────────────────────────
-- Your source JSON may use a/b/c/d for correct_answer.
-- The import maps them to 1/2/3/4 automatically.
-- Uppercase (A/B/C/D) is also handled.
--
-- [
--   {
--     "topic": "...",
--     "question": "...",
--     "option_a": "...",
--     "option_b": "...",
--     "option_c": "...",
--     "option_d": "...",
--     "correct_answer": "b"
--   },
--   ...
-- ]
-- ============================================================

INSERT INTO questions (topic, question, option_a, option_b, option_c, option_d, correct_answer)
SELECT
    (q->>'topic')::TEXT,
    (q->>'question')::TEXT,
    (q->>'option_a')::TEXT,
    (q->>'option_b')::TEXT,
    (q->>'option_c')::TEXT,
    (q->>'option_d')::TEXT,
    CASE lower(q->>'correct_answer')
        WHEN 'a' THEN '1'
        WHEN 'b' THEN '2'
        WHEN 'c' THEN '3'
        WHEN 'd' THEN '4'
        ELSE lower(q->>'correct_answer')   -- already '1'–'4', pass through
    END::CHAR(1)
FROM jsonb_array_elements(
    -- ↓ Replace everything between the single-quotes with your JSON array
    $$[
  {
    "question": "חברת נוקיה התמקדה במשך שנים בשיפור מתמיד של הטלפונים הקומפקטיים שלה, אך התעלמה מהמעבר של הצרכנים לטכנולוגיה מתקדמת יותר ובסופו של דבר איבדה את מעמדה בשוק. זוהי דוגמה לחיסרון המרכזי של גישת:",
    "option_a": "שיווק ממוקד מוצר",
    "option_b": "שיווק ממוקד לקוח",
    "option_c": "שיווק חוויתי",
    "option_d": "גישת המכירות",
    "correct_answer": "a",
    "topic": "גישות שיווק"
  },
  {
    "question": "חברת תרופות בוחנת את החקיקה הצפויה במדינה בה היא שוקלת להיכנס, כדי להבין אילו הגבלות עשויות לחול על שיווק התרופות שלה בעתיד. איזה גורם סביבתי היא בוחנת?",
    "option_a": "גורם דמוגרפי",
    "option_b": "גורם מדיני/חוקי",
    "option_c": "גורם חברתי/תרבותי",
    "option_d": "חסם כניסה",
    "correct_answer": "b",
    "topic": "ניתוח סביבה חיצונית - מאקרו"
  },
  {
    "question": "רשת בתי קולנוע מבחינה כי יותר ויותר צרכנים מעדיפים לצפות בסרטים בשירותי סטרימינג בבית, במקום לצאת לקולנוע. מנקודת מבטה של הרשת, שירותי הסטרימינג מהווים:",
    "option_a": "חסם כניסה",
    "option_b": "חסם יציאה",
    "option_c": "מוצר תחליפי",
    "option_d": "ספק",
    "correct_answer": "c",
    "topic": "ניתוח סביבה חיצונית - מיקרו"
  },
  {
    "question": "מנהל שיווק הבוחן אילו יכולות פנימיות יש לחברה שלו שיאפשרו לה לספק את צרכי הלקוחות טוב יותר מהמתחרים, מבצע למעשה:",
    "option_a": "Customer Analysis",
    "option_b": "Competitive Analysis",
    "option_c": "Company Analysis",
    "option_d": "ניתוח SWOT",
    "correct_answer": "c",
    "topic": "מודל 3C"
  },
  {
    "question": "עבור רשת קמעונאית מקוונת, העובדה שאין לה נקודות מכירה פיזיות ושאינה יכולה ליצור קשר אישי עם הלקוח, מסווגת במודל SWOT כ:",
    "option_a": "הזדמנות",
    "option_b": "איום",
    "option_c": "חולשה",
    "option_d": "חוזקה",
    "correct_answer": "c",
    "topic": "מודל SWOT"
  },
  {
    "question": "מנהלת שיווק קבעה יעד להגדלת המכירות, ולפני אישורו בדקה האם יש לחברה מספיק תקציב וכוח אדם להשגתו. איזה מרכיב במודל SMART היא בודקת?",
    "option_a": "Specific",
    "option_b": "Measurable",
    "option_c": "Achievable",
    "option_d": "Relevant",
    "correct_answer": "c",
    "topic": "מודל SMART"
  },
  {
    "question": "קו מוצרים של חברת מזון מאופיין בנתח שוק יחסי גבוה בשוק שקצב הצמיחה שלו נמוך, ומייצר לחברה יותר כסף ממה שמושקע בו. לפי מטריצת BCG, קו מוצרים זה מסווג כ:",
    "option_a": "Star",
    "option_b": "Question Mark",
    "option_c": "Cash Cow",
    "option_d": "Dog",
    "correct_answer": "c",
    "topic": "מטריצת BCG"
  },
  {
    "question": "רשת הסעדה ישראלית פתחה סניפים בלונדון, ומוכרת בהם את אותו התפריט המוכר שמופעל בסניפיה בישראל. לפי מטריצת Ansoff, מהלך זה הוא אסטרטגיית:",
    "option_a": "Market Penetration",
    "option_b": "Market Development",
    "option_c": "Product Development",
    "option_d": "Diversification",
    "correct_answer": "b",
    "topic": "מטריצת Ansoff"
  },
  {
    "question": "חברת ביגוד המחלקת את לקוחותיה הפוטנציאליים לפי תחומי עניין, ערכים ואורח חיים, מבצעת סגמנטציה מסוג:",
    "option_a": "דמוגרפית",
    "option_b": "גיאוגרפית",
    "option_c": "פסיכוגרפית",
    "option_d": "התנהגותית",
    "correct_answer": "c",
    "topic": "פילוח שוק (סגמנטציה)"
  },
  {
    "question": "חברת קוסמטיקה שמתאימה הצעה שיווקית שונה לכל אחד משלושת פלחי השוק הגדולים שאיתרה, נוקטת באסטרטגיית כיסוי הנקראת:",
    "option_a": "שיווק לא מבודל/המוני",
    "option_b": "שיווק מבודל",
    "option_c": "שיווק מרוכז/ממוקד",
    "option_d": "Micromarketing",
    "correct_answer": "b",
    "topic": "כיסוי שוק (טרגטינג)"
  },
  {
    "question": "חברת מזון העלתה מעט את איכות המוצר שלה, אך שמרה על אותו המחיר בדיוק כמו קודם לכן. מיצוב זה מתאים לאסטרטגיית:",
    "option_a": "More for More",
    "option_b": "More for the Same",
    "option_c": "The Same for Less",
    "option_d": "Less for Much Less",
    "correct_answer": "b",
    "topic": "מיצוב ובידול"
  },
  {
    "question": "העובדה שחברה יכולה לגבות מחיר גבוה יותר ממתחריה על מוצר דומה, רק בשל שמו המסחרי, נובעת בעיקר מ:",
    "option_a": "תפיסה (Perception)",
    "option_b": "נכסיות מותג גבוהה",
    "option_c": "אסוציאציות שליליות",
    "option_d": "דיסוננס קוגניטיבי",
    "correct_answer": "b",
    "topic": "נכסיות מותג"
  },
  {
    "question": "חברת תמי 4 השיקה דגם מתקן מים חדש, בעיצוב שונה מהדגמים הקיימים, תחת אותו שם מותג. מהלך זה מכונה:",
    "option_a": "הרחבת קו - Line Extension",
    "option_b": "מתיחת מותג - Brand Extension",
    "option_c": "ריבוי מותגים - Multibranding",
    "option_d": "מותג חדש - New Brand",
    "correct_answer": "a",
    "topic": "אסטרטגיות פיתוח מותג"
  },
  {
    "question": "רשת השיווק שופרסל מוכרת מוצרי מזון תחת המותג שופרסל עצמו, ולא תחת מותג של ספק חיצוני. סוג מותג זה מכונה:",
    "option_a": "מותג יצרן",
    "option_b": "מותג פרטי",
    "option_c": "מותג רישוי",
    "option_d": "מותג שיתופי",
    "correct_answer": "b",
    "topic": "בעלות על המותג"
  },
  {
    "question": "לפני שמתחילים לאסוף נתונים בפועל, על צוות המחקר לקבוע אילו נתונים נדרשים, מה התקציב והזמן העומדים לרשותו וכיצד ייאספו הנתונים. שלב זה בתהליך המחקר השיווקי נקרא:",
    "option_a": "הגדרת הבעיה",
    "option_b": "תכנון תוכנית המחקר",
    "option_c": "איסוף הנתונים",
    "option_d": "פירוש הנתונים ודיווח הממצאים",
    "correct_answer": "b",
    "topic": "תהליך המחקר השיווקי"
  },
  {
    "question": "חברת משקאות ביצעה ניסוי שבו הציגה לשתי קבוצות לקוחות שני סוגי אריזה שונים, על מנת לבדוק אם סוג האריזה משפיע על כמות הרכישה. זהו מחקר:",
    "option_a": "גישוש",
    "option_b": "תיאורי",
    "option_c": "סיבתי",
    "option_d": "משני",
    "correct_answer": "c",
    "topic": "סוגי מחקר שיווקי"
  },
  {
    "question": "חברה הקובעת את מחיר המוצר שלה בהתאם לתפיסת הלקוחות את הערך שהמוצר מספק להם, ולא בהתאם לעלויות הייצור, מיישמת שיטת:",
    "option_a": "תמחור מבוסס עלות",
    "option_b": "תמחור מבוסס תחרות",
    "option_c": "תמחור מבוסס ערך",
    "option_d": "Break Even Pricing",
    "correct_answer": "c",
    "topic": "אסטרטגיות תמחור"
  },
  {
    "question": "חברת אלקטרוניקה המשיקה מוצר חדשני וייחודי, וקובעת לו מחיר גבוה במיוחד בתחילת חייו מתוך כוונה להורידו בהדרגה עם הזמן, נוקטת באסטרטגיית:",
    "option_a": "חדירה לשוק",
    "option_b": "גריפת שוק",
    "option_c": "תמחור מבוסס תחרות",
    "option_d": "תמחור גיאוגרפי",
    "correct_answer": "b",
    "topic": "תמחור מוצר חדש"
  },
  {
    "question": "כלי קידום שמאפשר אינטראקציה ישירה ודו-כיוונית בין איש מכירות ללקוח, ונחשב לאפקטיבי ביותר בהובלה לפעולה אך גם לכלי הקידום היקר ביותר, הוא:",
    "option_a": "פרסום",
    "option_b": "מכירה אישית",
    "option_c": "קידום מכירות",
    "option_d": "יחסי ציבור",
    "correct_answer": "b",
    "topic": "תמהיל הקידום"
  },
  {
    "question": "חברת רכב הקובעת תקציב פרסום על סמך הגדרת יעדי קידום מסוימים ופירוט המשימות הנדרשות להשגתם, משתמשת בשיטת קביעת תקציב הנקראת:",
    "option_a": "שיטת ה'ניתן להרשות לעצמנו'",
    "option_b": "שיטת אחוז מהמכירות",
    "option_c": "שיטת ההשוואה למתחרים",
    "option_d": "שיטת המטרה והמשימה",
    "correct_answer": "d",
    "topic": "תהליך הפרסום"
  },
  {
    "question": "יצרן המשקיע באמצעי שיווק שמטרתם לגרום לצרכנים הסופיים לדרוש את המוצר מהקמעונאים, ובכך ל'משוך' את המוצר במורד שרשרת ההפצה, נוקט באסטרטגיית:",
    "option_a": "דחיפה",
    "option_b": "משיכה",
    "option_c": "קומבינציית דחיפה ומשיכה",
    "option_d": "הפצה אינטנסיבית",
    "correct_answer": "b",
    "topic": "אסטרטגיות דחיפה ומשיכה"
  },
  {
    "question": "כאשר לקוחות מרוצים משתפים בעצמם תוכן חיובי על מוצר ברשתות החברתיות, ללא תשלום מהחברה, סוג המדיה הדיגיטלית מכונה:",
    "option_a": "Owned Media",
    "option_b": "Paid Media",
    "option_c": "Earned Media",
    "option_d": "Display Advertising",
    "correct_answer": "c",
    "topic": "שיווק דיגיטלי"
  },
  {
    "question": "מוצר שנמצא בשלב בו המכירות בירידה מתמשכת, החברה מצמצמת את הוצאות הפרסום לרמה מינימלית ובוחנת ביטול בשלבים של פריטים חלשים מתוך קו המוצרים, נמצא ב:",
    "option_a": "שלב ההצגה",
    "option_b": "שלב הצמיחה",
    "option_c": "שלב הבגרות",
    "option_d": "שלב הדעיכה",
    "correct_answer": "d",
    "topic": "מחזור חיי המוצר"
  },
  {
    "question": "ביטוח חיים נחשב למוצר שהצרכנים בדרך כלל לא חושבים לקנות בעצמם, ולכן הוא מצריך מכירה אישית ופרסום אינטנסיביים. סיווג זה הוא של:",
    "option_a": "מוצר נוחות",
    "option_b": "מוצר חיפוש",
    "option_c": "מוצר ייחוד/התמחות",
    "option_d": "מוצר לא נדרש",
    "correct_answer": "d",
    "topic": "סיווג מוצרי צריכה"
  },
  {
    "question": "סטודנט שמעדיף לקנות סניקרס ממותג מסוים כי הוא משתייך לקבוצת חברים שכולם נועלים את אותו המותג, מודגמת השפעה של:",
    "option_a": "גורם תרבותי",
    "option_b": "קבוצת התייחסות",
    "option_c": "גורם פסיכולוגי",
    "option_d": "תפיסה",
    "correct_answer": "b",
    "topic": "התנהגות צרכנים - גורמים משפיעים"
  },
  {
    "question": "לאחר רכישת רכב חדש, הלקוח מתחיל לחשוש שטעה בבחירתו, ומחפש מידע נוסף שיחזק את ההחלטה שלקח. מצב זה מכונה:",
    "option_a": "הערכת חלופות",
    "option_b": "דיסוננס קוגניטיבי",
    "option_c": "סילוף בררני",
    "option_d": "קשב בררני",
    "correct_answer": "b",
    "topic": "התנהגות שלאחר רכישה"
  },
  {
    "question": "צרכן השוקל לקנות טלוויזיה, ונוטה לבחור בדגם שאינו הזול ביותר ואינו היקר ביותר מבין האפשרויות שבחר להתלבט ביניהן, ממחיש את:",
    "option_a": "אפקט העיגון",
    "option_b": "אפקט הפשרה",
    "option_c": "קשב בררני",
    "option_d": "המודל המפצה",
    "correct_answer": "b",
    "topic": "הטיות בקבלת החלטות"
  }
]$$::jsonb
) AS q;

-- Verify the import
SELECT COUNT(*) AS imported_questions FROM questions;
