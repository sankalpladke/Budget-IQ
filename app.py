from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# File paths
EXPENSES_FILE = 'data/expenses.xlsx'
BUDGET_FILE = 'data/budget.xlsx'
os.makedirs('data', exist_ok=True)

if not os.path.exists(EXPENSES_FILE):
    pd.DataFrame(columns=['Date', 'Category', 'Amount', 'Description']).to_excel(EXPENSES_FILE, index=False, engine='openpyxl')

if not os.path.exists(BUDGET_FILE):
    pd.DataFrame(columns=['Month', 'Category', 'Budget']).to_excel(BUDGET_FILE, index=False, engine='openpyxl')

# Chart generation

def create_bar_chart(data, title):
    fig, ax = plt.subplots()
    categories = list(data.keys())
    values = list(data.values())
    ax.bar(categories, values, color='skyblue')
    ax.set_title(title)
    ax.set_ylabel('Amount')
    ax.set_xlabel('Category')
    plt.xticks(rotation=45, ha='right')
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig)
    return encoded

@app.route('/')
def index():
    try:
        exp_df = pd.read_excel(EXPENSES_FILE, engine='openpyxl')
        total_expense = exp_df['Amount'].sum()
        expense_summary = exp_df.groupby('Category')['Amount'].sum().to_dict()
    except:
        exp_df = pd.DataFrame()
        total_expense = 0
        expense_summary = {}

    try:
        bud_df = pd.read_excel(BUDGET_FILE, engine='openpyxl')
        total_budget = bud_df['Budget'].sum()
        budget_summary = bud_df.groupby('Category')['Budget'].sum().to_dict()
    except:
        bud_df = pd.DataFrame()
        total_budget = 0
        budget_summary = {}

    return render_template('index.html', total=total_expense, total_budget=total_budget,
                           summary=expense_summary, budget_summary=budget_summary)

@app.route('/charts')
def charts():
    try:
        exp_df = pd.read_excel(EXPENSES_FILE, engine='openpyxl')
        expense_summary = exp_df.groupby('Category')['Amount'].sum().to_dict()
    except:
        expense_summary = {}

    try:
        bud_df = pd.read_excel(BUDGET_FILE, engine='openpyxl')
        budget_summary = bud_df.groupby('Category')['Budget'].sum().to_dict()
    except:
        budget_summary = {}

    expense_chart = create_bar_chart(expense_summary, "Expenses by Category")
    budget_chart = create_bar_chart(budget_summary, "Budgets by Category")

    return render_template('charts.html', expense_chart=expense_chart, budget_chart=budget_chart)

@app.route('/add-expense', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        new_data = pd.DataFrame([{
            'Date': request.form['date'],
            'Category': request.form['category'],
            'Amount': float(request.form['amount']),
            'Description': request.form['description']
        }])
        df = pd.read_excel(EXPENSES_FILE, engine='openpyxl')
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_excel(EXPENSES_FILE, index=False, engine='openpyxl')
        return redirect('/')
    return render_template('add_expense.html')

@app.route('/view-expenses')
def view_expenses():
    df = pd.read_excel(EXPENSES_FILE, engine='openpyxl')
    df = df.reset_index().rename(columns={'index': 'ID'})
    expenses = df.to_dict(orient='records')
    return render_template('view_expenses.html', expenses=expenses)

@app.route('/edit-expense/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    df = pd.read_excel(EXPENSES_FILE, engine='openpyxl')
    if request.method == 'POST':
        df.loc[id, 'Date'] = request.form['date']
        df.loc[id, 'Category'] = request.form['category']
        df.loc[id, 'Amount'] = float(request.form['amount'])
        df.loc[id, 'Description'] = request.form['description']
        df.to_excel(EXPENSES_FILE, index=False, engine='openpyxl')
        return redirect('/view-expenses')
    row = df.iloc[id]
    return render_template('edit_expense.html', expense=row, id=id)

@app.route('/delete-expense/<int:id>')
def delete_expense(id):
    df = pd.read_excel(EXPENSES_FILE, engine='openpyxl')
    df = df.drop(index=id).reset_index(drop=True)
    df.to_excel(EXPENSES_FILE, index=False, engine='openpyxl')
    return redirect('/view-expenses')

@app.route('/add-budget', methods=['GET', 'POST'])
def add_budget():
    if request.method == 'POST':
        new_data = pd.DataFrame([{
            'Month': request.form['month'],
            'Category': request.form['category'],
            'Budget': float(request.form['budget'])
        }])
        df = pd.read_excel(BUDGET_FILE, engine='openpyxl')
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_excel(BUDGET_FILE, index=False, engine='openpyxl')
        return redirect('/')
    return render_template('add_budget.html')

@app.route('/reports')
def reports():
    df = pd.read_excel(BUDGET_FILE, engine='openpyxl')
    df = df.reset_index().rename(columns={'index': 'ID'})
    if not df.empty:
        df = df.rename(columns={'Category': 'BudgetCategory', 'Budget': 'BudgetAmount'})
    records = df.to_dict(orient='records')
    return render_template('reports.html', budgets=records)

@app.route('/edit-budget/<int:id>', methods=['GET', 'POST'])
def edit_budget(id):
    df = pd.read_excel(BUDGET_FILE, engine='openpyxl')
    if request.method == 'POST':
        df.loc[id, 'Month'] = request.form['month']
        df.loc[id, 'Category'] = request.form['category']
        df.loc[id, 'Budget'] = float(request.form['budget'])
        df.to_excel(BUDGET_FILE, index=False, engine='openpyxl')
        return redirect('/reports')
    record = df.iloc[id]
    return render_template('edit_budget.html', budget=record, id=id)

@app.route('/delete-budget/<int:id>')
def delete_budget(id):
    df = pd.read_excel(BUDGET_FILE, engine='openpyxl')
    df = df.drop(index=id).reset_index(drop=True)
    df.to_excel(BUDGET_FILE, index=False, engine='openpyxl')
    return redirect('/reports')

if __name__ == '__main__':
    app.run(debug=True)
