import pandas as pd
import csv
import streamlit as st
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns


class CSV:
    CSV_FILE = "finance_data.csv"
    COLUMNS = ["date", "amount", "category", "description"]
    FORMAT = "%d-%m-%Y"

    @classmethod
    def initialize_csv(cls):
        try:
            pd.read_csv(cls.CSV_FILE)
        except FileNotFoundError:
            df = pd.DataFrame(columns=cls.COLUMNS)
            df.to_csv(cls.CSV_FILE, index=False)

    @classmethod
    def add_entry(cls, date, amount, category, description):
        new_entry = {
            "date": date,
            "amount": amount,
            "category": category,
            "description": description,
        }
        with open(cls.CSV_FILE, "a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=cls.COLUMNS)
            writer.writerow(new_entry)
        st.success("Entry added successfully")

    @classmethod
    def get_transactions(cls, start_date, end_date):
        df = pd.read_csv(cls.CSV_FILE)
        df["date"] = pd.to_datetime(df["date"], format=CSV.FORMAT)
        start_date = datetime.strptime(start_date, CSV.FORMAT)
        end_date = datetime.strptime(end_date, CSV.FORMAT)

        mask = (df["date"] >= start_date) & (df["date"] <= end_date)
        filtered_df = df.loc[mask]

        return filtered_df


def create_visualizations(df):
    if df.empty:
        st.warning("No transactions available for plotting.")
        return

    # Ensure proper data types
    df["date"] = pd.to_datetime(df["date"], format=CSV.FORMAT)
    df["amount"] = df["amount"].astype(float)
    
    # Create a copy of the dataframe with date as index for time-based visualizations
    df_indexed = df.copy()
    df_indexed.set_index("date", inplace=True)

    # Visualization options
    st.subheader("Visualization Options")
    viz_type = st.selectbox(
        "Select Visualization Type",
        ["Time Series", "Category Breakdown", "Income vs Expense", "Daily/Monthly Analysis"]
    )

    if viz_type == "Time Series":
        chart_type = st.selectbox("Select Chart Type", ["Line", "Bar"])
        
        # Group data by category and date
        income_df = df_indexed[df_indexed["category"] == "Income"].resample("D").sum()
        expense_df = df_indexed[df_indexed["category"] == "Expense"].resample("D").sum()
        
        plt.figure(figsize=(12, 6))
        
        if chart_type == "Line":
            plt.plot(income_df.index, income_df["amount"], label="Income", color="green", marker="o")
            plt.plot(expense_df.index, expense_df["amount"], label="Expense", color="red", marker="x")
        else:  # Bar
            width = 0.35
            if not income_df.empty:
                plt.bar(income_df.index, income_df["amount"], width=width, label="Income", color="green", alpha=0.7)
            if not expense_df.empty:
                plt.bar(expense_df.index, expense_df["amount"], width=width, label="Expense", color="red", alpha=0.7)
        
        plt.xlabel("Date")
        plt.ylabel("Amount (₹)")
        plt.title(f"{chart_type} Chart: Income and Expenses Over Time")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(plt)
        plt.close()

    elif viz_type == "Category Breakdown":
        chart_type = st.selectbox("Select Chart Type", ["Pie", "Bar"])
        
        # Allow user to select Income or Expense for breakdown
        category_filter = st.selectbox("Select Category", ["Income", "Expense"])
        filtered_data = df[df["category"] == category_filter]
        
        if filtered_data.empty:
            st.warning(f"No {category_filter} data available for the selected period.")
            return
            
        # Group by description for sub-category analysis
        grouped_data = filtered_data.groupby("description")["amount"].sum().reset_index()
        
        plt.figure(figsize=(10, 6))
        
        if chart_type == "Pie":
            plt.pie(
                grouped_data["amount"], 
                labels=grouped_data["description"],
                autopct='%1.1f%%', 
                startangle=90,
                shadow=True
            )
            plt.axis('equal')
            plt.title(f"Breakdown of {category_filter} by Category")
        else:  # Bar
            sns.barplot(x="description", y="amount", data=grouped_data)
            plt.xlabel("Category")
            plt.ylabel("Amount (₹)")
            plt.title(f"Breakdown of {category_filter} by Category")
            plt.xticks(rotation=45)
            plt.tight_layout()
        
        st.pyplot(plt)
        plt.close()

    elif viz_type == "Income vs Expense":
        # Calculate totals
        total_income = df[df["category"] == "Income"]["amount"].sum()
        total_expense = df[df["category"] == "Expense"]["amount"].sum()
        
        # Create comparison visualizations
        chart_type = st.selectbox("Select Chart Type", ["Bar", "Pie"])
        
        labels = ["Income", "Expense"]
        values = [total_income, total_expense]
        
        plt.figure(figsize=(8, 6))
        
        if chart_type == "Bar":
            plt.bar(labels, values, color=["green", "red"])
            plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
            plt.grid(axis='y', alpha=0.3)
            for i, v in enumerate(values):
                plt.text(i, v + 50, f"₹{v:.2f}", ha='center')
        else:  # Pie
            plt.pie(
                values, 
                labels=labels,
                autopct='%1.1f%%', 
                startangle=90,
                colors=["green", "red"],
                shadow=True
            )
            plt.axis('equal')
        
        plt.title("Total Income vs Expense")
        st.pyplot(plt)
        plt.close()
        
        # Display savings calculation
        savings = total_income - total_expense
        savings_percent = (savings / total_income * 100) if total_income > 0 else 0
        
        col1, col2 = st.columns(2)
        col1.metric("Net Savings", f"₹{savings:.2f}")
        col2.metric("Savings Rate", f"{savings_percent:.1f}%")

    elif viz_type == "Daily/Monthly Analysis":
        time_period = st.selectbox("Select Time Period", ["Daily", "Monthly"])
        chart_type = st.selectbox("Select Chart Type", ["Line", "Bar"])
        
        # Resample based on selected time period
        if time_period == "Daily":
            income_ts = df_indexed[df_indexed["category"] == "Income"].resample("D").sum()
            expense_ts = df_indexed[df_indexed["category"] == "Expense"].resample("D").sum()
            title_period = "Daily"
        else:  # Monthly
            income_ts = df_indexed[df_indexed["category"] == "Income"].resample("M").sum()
            expense_ts = df_indexed[df_indexed["category"] == "Expense"].resample("M").sum()
            title_period = "Monthly"
        
        # Create a combined dataframe for the plot
        combined_df = pd.DataFrame({
            'Income': income_ts["amount"] if not income_ts.empty else 0,
            'Expense': expense_ts["amount"] if not expense_ts.empty else 0
        })
        
        # Calculate net savings
        combined_df['Net'] = combined_df['Income'] - combined_df['Expense']
        
        plt.figure(figsize=(12, 6))
        
        if chart_type == "Line":
            plt.plot(combined_df.index, combined_df['Income'], 'g-', label='Income')
            plt.plot(combined_df.index, combined_df['Expense'], 'r-', label='Expense')
            plt.plot(combined_df.index, combined_df['Net'], 'b--', label='Net')
        else:  # Bar
            combined_df.plot(kind='bar', figsize=(12, 6))
            
        plt.title(f"{title_period} Financial Analysis")
        plt.xlabel("Date")
        plt.ylabel("Amount (₹)")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        st.pyplot(plt)
        plt.close()


def main():
    st.title("Personal Finance Tracker")
    CSV.initialize_csv()
    
    menu = ["Add Transaction", "View Transactions", "Analytics Dashboard"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Add Transaction":
        st.subheader("Add a New Transaction")
        date = st.date_input("Select Date", datetime.today()).strftime(CSV.FORMAT)
        amount = st.number_input("Enter Amount", min_value=0.0, format="%.2f")
        category = st.selectbox("Category", ["Income", "Expense"])
        description = st.text_input("Description")
        
        if st.button("Add Transaction"):
            CSV.add_entry(date, amount, category, description)
    
    elif choice == "View Transactions":
        st.subheader("View Transactions in a Date Range")
        start_date = st.date_input("Start Date").strftime(CSV.FORMAT)
        end_date = st.date_input("End Date").strftime(CSV.FORMAT)
        
        if st.button("Show Transactions"):
            df = CSV.get_transactions(start_date, end_date)
            if df.empty:
                st.warning("No transactions found in the given date range.")
            else:
                st.dataframe(df)
                total_income = df[df["category"] == "Income"]["amount"].sum()
                total_expense = df[df["category"] == "Expense"]["amount"].sum()
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Income", f"₹{total_income:.2f}")
                col2.metric("Total Expense", f"₹{total_expense:.2f}")
                col3.metric("Net Savings", f"₹{(total_income - total_expense):.2f}")
                
                # Show visualization options
                create_visualizations(df)
    
    elif choice == "Analytics Dashboard":
        st.subheader("Financial Analytics Dashboard")
        
        # Date range selection
        st.write("Select Date Range for Analysis:")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.today().replace(day=1)).strftime(CSV.FORMAT)
        with col2:
            end_date = st.date_input("End Date", datetime.today()).strftime(CSV.FORMAT)
        
        # Get transaction data
        df = CSV.get_transactions(start_date, end_date)
        
        if df.empty:
            st.warning("No transactions found in the given date range.")
        else:
            # Summary metrics
            total_income = df[df["category"] == "Income"]["amount"].sum()
            total_expense = df[df["category"] == "Expense"]["amount"].sum()
            balance = total_income - total_expense
            
            # Create 3 columns for metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Income", f"₹{total_income:.2f}")
            col2.metric("Total Expense", f"₹{total_expense:.2f}")
            col3.metric("Balance", f"₹{balance:.2f}", delta=f"{(balance/total_income*100):.1f}%" if total_income > 0 else "0%")
            
            # Create visualizations
            create_visualizations(df)


if __name__ == "__main__":
    main()