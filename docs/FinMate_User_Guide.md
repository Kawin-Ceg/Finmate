# FinMate — User Guide

## Welcome to FinMate

FinMate is an AI-powered personal finance management platform that helps you understand where your money goes. Import your bank statement CSV, and FinMate automatically categorizes every transaction, tracks your budgets, and generates a financial health score with personalized insights.

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Landing Page](#2-landing-page)
3. [Creating an Account](#3-creating-an-account)
4. [Logging In](#4-logging-in)
5. [Dashboard Overview](#5-dashboard-overview)
6. [Uploading Transactions](#6-uploading-transactions)
7. [Transactions Page](#7-transactions-page)
8. [Analytics Page](#8-analytics-page)
9. [Budgets Page](#9-budgets-page)
10. [Understanding Your Financial Health Score](#10-understanding-your-financial-health-score)
11. [Supported CSV Formats](#11-supported-csv-formats)
12. [Frequently Asked Questions](#12-frequently-asked-questions)

---

## 1. Getting Started

To use FinMate, you need:
- A modern web browser (Chrome, Firefox, Edge, Safari)
- A bank statement in CSV format (download from your bank's internet banking portal)
- The application running locally (or deployed URL)

**Default URL (local):** `http://localhost:5173`

---

## 2. Landing Page

The landing page introduces FinMate and its key capabilities. It is publicly accessible — no account required.

**Sections on the landing page:**
- **Hero** — Value proposition with "Get Started" CTA
- **Features** — Three key capabilities: AI categorization, real-time analytics, budget tracking
- **How It Works** — 3-step onboarding: Upload Statement → Auto-categorize → Get Insights
- **AI Showcase** — Preview of the analytics and health score system
- **Trust Section** — Security and privacy messaging
- **CTA Section** — Sign-up call to action
- **Footer** — Navigation links

**Navigation from landing page:**
- Click **"Get Started"** → `/signup`
- Click **"Login"** (top nav) → `/login`

---

## 3. Creating an Account

**Route:** `/signup`

1. Enter your **full name** (displayed in the sidebar)
2. Enter your **email address** (used for login)
3. Enter a **password** (minimum recommended: 8 characters)
4. Confirm your password
5. Accept the terms of service
6. Click **"Create Account"**

**Notes:**
- Each email address can only be registered once
- Passwords are stored as secure bcrypt hashes — never in plain text
- You are automatically redirected to `/login` after successful signup

**Already have an account?** Click "Sign in" below the form.

---

## 4. Logging In

**Route:** `/login`

1. Enter your **email address**
2. Enter your **password**
3. Click **"Sign In"**

On success, you are redirected to `/dashboard`.

Your session is stored in your browser (`localStorage`) and persists across page refreshes. You remain logged in until you click **"Sign Out"** in the sidebar.

**Forgot password?** Password reset is not currently implemented.

---

## 5. Dashboard Overview

**Route:** `/dashboard`

The dashboard is your home screen inside FinMate. It shows a high-level summary of your financial data.

### Stats Cards (Top Row)

| Card | What It Shows |
|------|--------------|
| **Monthly Spending** | Total debit transactions across all imported data |
| **Net Savings** | Total income minus total spending |
| **Top Category** | Category where you spend the most |
| **Transactions** | Total number of imported records |

### Spending Chart

An area chart showing your monthly spending trend. This chart helps you spot months where spending spiked.

### AI Insights

Sample financial insights appear here. As more of your data is analyzed, this section will show personalized recommendations about your spending patterns.

### Recent Transactions

The 5 most recent transactions are shown in a mini-table. Click the **"View All"** button or navigate to **Transactions** in the sidebar to see the full list.

### Budget Progress

A quick view of your budget utilization. Create budgets on the **Budgets** page to see real data here.

---

## 6. Uploading Transactions

**How to upload:** Click the **"Upload Statement"** button (top-right of Transactions page, or on the dashboard).

### Step-by-Step Upload Process

1. Click **"Upload Statement"**
2. The upload modal opens
3. **Drag and drop** your CSV file onto the upload area, or click **"Browse"** to select a file
4. FinMate shows the selected filename and size
5. Click **"Upload"**
6. A progress indicator appears while the file is being processed
7. On success, you see: **"Successfully imported X transactions"**
8. The transactions table refreshes automatically

### What Happens During Upload

1. The file is sent to the backend
2. FinMate auto-detects your CSV column names (supports HDFC, SBI, ICICI, Axis Bank, and many others)
3. Each transaction row is parsed for date, merchant name, and amount
4. The **ML categorizer** predicts a spending category using a trained XGBoost model
5. If the model's confidence is below 60%, a **rule-based fallback** assigns the category
6. All transactions are stored in your account

### Common Upload Errors

| Error | Solution |
|-------|---------|
| "Only CSV files are accepted" | Convert your file to CSV format first |
| "CSV missing a date column" | Check that your CSV has a column named `date`, `txn_date`, or similar |
| "CSV missing a merchant column" | Your file needs a `merchant`, `narration`, or `particulars` column |
| "No valid transactions found" | Check that your CSV has actual data rows with valid dates and amounts |
| "Unable to decode file" | Open in Excel, File → Save As → CSV UTF-8, then try again |

---

## 7. Transactions Page

**Route:** `/dashboard/transactions`

This is the main transaction management page.

### Stats Row

Four summary cards at the top:
- **Total Spending** — all-time debit total
- **Total Income** — all-time credit total
- **Top Category** — highest spend category
- **Transactions** — total count

### Search and Filters

| Control | Function |
|---------|---------|
| Search box | Search merchant names, descriptions, or categories |
| Category dropdown | Filter by a specific category |
| Month dropdown | Filter by month (January–December) |
| Year dropdown | Filter by year (last 5 years) |

Filters can be combined (e.g., show all "Food" transactions in "January 2025").

### Transaction Table

Each row shows:
- **Date** — formatted as "1 Jan 2025"
- **Merchant** — the business or payee name
- **Category** — colored badge (e.g., green for Income, orange for Food)
- **ML Confidence** — small percentage shown next to the badge (e.g., `98%`) when the ML model categorized the transaction; no percentage shown when rule engine was used
- **Amount** — formatted in Indian currency (e.g., `₹3,500`)
- **Type** — green "Credit" or red "Debit" badge

### Pagination

Transactions are paginated at 20 per page. Use **Previous** and **Next** buttons at the bottom to navigate. The total count is shown on the left.

### Understanding the Category Confidence Badge

When you see `[Food]  98%` next to a transaction:
- The **ML model** categorized this transaction
- It is **98% confident** this is a food transaction
- A high confidence score means the model found strong text signals

When you see `[Transport]` without a percentage:
- The **rule engine** categorized this transaction
- This happens when the ML model's confidence was below 60%
- The rule engine matched a keyword like "uber" or "auto"

---

## 8. Analytics Page

**Route:** `/dashboard/analytics`

The analytics page gives you a comprehensive view of your financial patterns.

### Row 1: Health Score + Overview Stats

**Financial Health Score** (left panel):
- A score from 0 to 100 with a letter grade (A+ to D)
- Four component scores shown as progress bars
- See [Section 10](#10-understanding-your-financial-health-score) for full explanation

**Overview Stats** (right panel):
- Total Income (all time)
- Total Expenses (all time)
- Net Savings
- Savings Rate (% of income saved)

### Row 2: Monthly Spending Trend

An area chart showing your spending month by month for the last 12 months. Hover over any month to see the exact amount.

**How to read it:** Rising months indicate increased spending; flat or declining months show good discipline.

### Row 3: Category Breakdown + Top Merchants

**Category Breakdown** (left): A donut chart + table showing what percentage of your spending goes to each category. Hover over chart segments for exact amounts.

**Top Merchants** (right): The 5 businesses or payees where you spend the most money.

### Row 4: Cash Flow Chart

A dual-area chart comparing your **income** (green) vs **expenses** (red) month by month. When the green area is higher, you saved money that month.

### Row 5: Spending Heatmap + Health Insights

**Spending Heatmap** (left): A bar chart showing your average spending per transaction on each day of the week. If Saturday/Sunday bars are much taller, you spend significantly more on weekends.

**Health Insights** (right): Personalized text observations generated from your data, such as:
- "Savings rate of 27%. Aim for 20%+ for long-term security."
- "Monthly expenses are consistent — a sign of disciplined spending."
- "Weekend spending is 2.3× higher than weekday average."

---

## 9. Budgets Page

**Route:** `/dashboard/budgets`

Budgets let you set monthly spending caps per category and track whether you're on track.

### Overview Stats

| Card | Description |
|------|-------------|
| **Total Budget** | Sum of all your monthly budget limits |
| **Total Spent** | Actual spending this month across all budgeted categories |
| **Remaining** | How much budget is left this month |
| **At Risk** | Count of categories that are 85%+ of their limit |

### Budget Alerts

If any budget is projected to be exceeded or is already over 85%, alert banners appear at the top of the page with specific amounts and recommendations.

### Creating a Budget

1. Click **"Add Budget"**
2. Select a **category** from the dropdown (shows categories you haven't budgeted yet)
3. Enter a **monthly limit** in rupees
4. Click **"Create Budget"**

The budget immediately shows on the page with real-time spending data from your current month's transactions.

### Budget Cards

Each budget card shows:
- **Category name** + risk badge (Safe / Watch / High / Exceeded)
- **Progress bar** — colored by risk level
- **₹X,XXX / ₹X,XXX** — amount spent vs limit
- **Remaining** (or "Over by ₹X") below the bar
- **Edit** and **Delete** buttons

**Risk levels:**
| Color | Label | Meaning |
|-------|-------|---------|
| Green | Safe | Less than 60% of limit used |
| Yellow | Watch | 60–85% of limit used |
| Orange | High | 85–100% of limit used |
| Red | Exceeded | Over budget |

### Editing a Budget

Click the **Edit** (pencil) icon on a budget card to update the monthly limit. Category cannot be changed — delete and recreate if you need to change the category.

### Deleting a Budget

Click the **Delete** (trash) icon. The budget is permanently removed. Your transactions are not affected.

### Budget Forecast

At the bottom of the page, a forecast table shows projected end-of-month spending based on your current daily rate:

```
Category   Budget      Current   Projected   Overrun    Risk
─────────────────────────────────────────────────────────────
Food       ₹8,000     ₹5,200    ₹10,400     ₹2,400     Exceeded
Transport  ₹3,000     ₹900      ₹1,800      —          Safe
```

**How the projection works:** If you've spent ₹5,200 in 16 days of a 31-day month, your daily rate is ₹325. Projected spend = ₹325 × 31 = ₹10,075.

---

## 10. Understanding Your Financial Health Score

The Financial Health Score is a composite metric from 0 to 100 that summarizes the overall health of your finances based on four factors.

### Score Components

| Component | Max Points | What It Measures |
|-----------|-----------|----------------|
| Savings Rate | 35 | What % of your income do you save? (30% = full score) |
| Expense Stability | 25 | How consistent is your monthly spending? |
| Income Consistency | 25 | How stable is your monthly income? |
| Category Diversification | 15 | Is your spending spread across categories? |

### Grade Scale

| Score | Grade | Status |
|-------|-------|--------|
| 90–100 | A+ | Excellent |
| 80–89 | A | Very Good |
| 70–79 | B | Good |
| 60–69 | C | Fair |
| 0–59 | D | Needs Improvement |

### How to Improve Your Score

| Low Component | Action |
|--------------|--------|
| Savings Rate | Review your top 3 spending categories and find reduction opportunities |
| Expense Stability | Create budgets to cap variable categories; automate fixed expenses |
| Income Consistency | If freelance/irregular income, aim for more retainer arrangements |
| Category Diversification | If one category dominates, check if it's necessary (rent is fine; excessive dining out may not be) |

### Insights Explained

The health score generates up to 5 personalized insights based on your data patterns:

| Insight | Trigger |
|---------|---------|
| "Excellent savings habit — saving X% of income" | savings_rate ≥ 25% |
| "Savings rate of X%. Aim for 20%+" | savings_rate between 10–25% |
| "Savings rate is under 10%. Review your spending." | income exists but savings < 10% |
| "Monthly expenses are consistent" | expense CV ≤ 35% |
| "Monthly expenses fluctuate significantly" | expense CV > 35% |
| "Income is highly consistent" | income CV < 15% |
| "Irregular income detected" | income CV > 40% |
| "[Category] accounts for X% of expenses" | top category > 40% of total expense |
| "Weekend spending is X× higher than weekday" | weekend avg > 1.5× weekday avg |

---

## 11. Supported CSV Formats

FinMate supports virtually any bank CSV format with flexible column detection. Tested formats include:

| Bank | Common Column Names |
|------|-------------------|
| HDFC Bank | Date, Narration, Amount |
| SBI | Date, Description, Debit, Credit |
| ICICI Bank | Transaction Date, Transaction Remarks, Amount |
| Axis Bank | Tran Date, Particulars, Debit/Credit |
| Kotak | Txn Date, Description, Dr/Cr |
| Custom export | Any combination of the recognized column names |

**Minimum requirements for a valid CSV:**
1. A date column (any format above)
2. A merchant/description column
3. Either an `amount` column OR separate `debit`/`credit` columns

**Sample minimum CSV:**
```csv
date,merchant,amount
01/01/2025,SWIGGY FOOD ORDER,350
05/01/2025,SALARY CREDIT,-50000
10/01/2025,ATM CASH WITHDRAWAL,2000
```

(Negative amounts → credit transactions; positive → debit)

---

## 12. Frequently Asked Questions

**Q: Is my financial data safe?**  
A: Your data is stored locally in a PostgreSQL database running on your own machine (or your server). FinMate does not send data to any external service.

**Q: Can I import multiple CSV files?**  
A: Yes. Upload as many CSV files as you want. Each upload appends transactions to your account. Duplicate detection is not implemented — avoid uploading the same file twice.

**Q: What if a transaction is categorized incorrectly?**  
A: Manual re-categorization is not available yet. In the meantime, the ML+rule hybrid system handles most common Indian merchants correctly. For incorrect categories, you can note them for a future retrain of the model.

**Q: Can I delete transactions?**  
A: Individual transaction deletion is not currently available. You can delete your entire account (via direct database access) to start fresh.

**Q: Why does some transactions show a confidence %, but others don't?**  
A: Transactions with a percentage (e.g., `98%`) were categorized by the ML model with high confidence. Transactions without a percentage were categorized by the keyword rule engine (used when ML confidence is below 60%).

**Q: The dashboard shows no data — what's wrong?**  
A: You need to upload at least one CSV file first. Go to Transactions → Upload Statement.

**Q: Can I add transactions manually?**  
A: Manual transaction entry is not currently implemented. All transactions must be imported via CSV upload.

**Q: What is the budget "forecast"?**  
A: The forecast projects your likely end-of-month spending based on your current daily spending rate. If you've spent ₹5,200 in 16 days, your daily rate is ₹325, and you're projected to spend ₹325 × 31 = ₹10,075 by month-end.

**Q: Why does my health score show 0?**  
A: You need transactions covering at least 2 months to get meaningful scores for the stability components. With only 1 month of data, Expense Stability and Income Consistency use default values of 20 pts each (out of 25 max).
