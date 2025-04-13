import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF

st.title("📊 Finance Report Generator")

# Company details input (outside the form so they’re always visible)
st.header("Company Details")
company_name = st.text_input("Enter Company's Name")
n = st.number_input("Enter number of products", min_value=1, step=1)
FC = st.number_input("Enter total fixed cost", min_value=0)

if company_name and n:
    # Group remaining inputs into a form
    with st.form("finance_form"):
        st.subheader("Enter Product Details")
        Names = []
        Sales = []
        VC = []
        # Loop dynamically based on n (converted to integer)
        for i in range(int(n)):
            st.markdown(f"**Product {i+1} Details**")
            # Use unique keys for each input widget
            prod_name = st.text_input(f"Name of product {i+1}", key=f"name_{i}")
            prod_sales = st.number_input(f"Selling price of product {i+1}", min_value=0, key=f"sales_{i}")
            prod_vc = st.number_input(f"Variable cost of product {i+1}", min_value=0, key=f"vc_{i}")
            Names.append(prod_name)
            Sales.append(prod_sales)
            VC.append(prod_vc)

        st.subheader("Supplier Evaluation")
        standard_price = st.number_input("Enter standard material price", min_value=0, key="std_price")
        actual_price = st.number_input("Enter actual material price", min_value=0, key="act_price")
        actual_quantity = st.number_input("Enter actual quantity purchased", min_value=0, key="act_qty")

        # Submit all inputs at once
        submit = st.form_submit_button("Generate Report")

    if submit:
        # Create DataFrame from product details
        company_data = pd.DataFrame({"Name": Names, "Sales": Sales, "VC": VC})
        company_data["Contribution"] = company_data["Sales"] - company_data["VC"]
        # Avoid division by zero using apply; set ratio to zero if Sales is 0.
        company_data["PV_ratio/unit"] = company_data.apply(
            lambda row: ((row["Sales"] - row["VC"]) / row["Sales"] * 100) if row["Sales"] > 0 else 0,
            axis=1
        )

        # Calculate totals and other financial metrics
        Total_sales = company_data["Sales"].sum()
        Total_vc = company_data["VC"].sum()
        PV_ratio = ((Total_sales - Total_vc) / Total_sales) * 100 if Total_sales > 0 else 0
        BEP = FC / (PV_ratio / 100) if PV_ratio > 0 else 0
        net_profit = Total_sales - (FC + Total_vc)

        # Display results
        st.subheader("📈 Product PV Ratios")
        fig, ax = plt.subplots()
        ax.bar(company_data["Name"], company_data["PV_ratio/unit"], color='red')
        ax.set_xlabel("Product Name")
        ax.set_ylabel("PV Ratio per Unit (%)")
        ax.set_title("Product PV Ratio Comparison")
        st.pyplot(fig)

        st.subheader("💼 Summary")
        st.write(f"**Company Name:** {company_name}")
        st.write(f"**Fixed Cost:** Rs. {FC}")
        st.write(f"**Total Sales:** Rs. {Total_sales}")
        st.write(f"**Net Profit:** Rs. {net_profit}")
        st.write(f"**Break Even Point:** Rs. {round(BEP, 2)}")

        stop_production = company_data[company_data["Contribution"] <= 0]["Name"].tolist()
        st.subheader("🛑 Products with Non-Positive Contribution")
        if stop_production:
            st.warning(f"Stop production of these products: {', '.join(stop_production)}")
        else:
            st.success("All products are profitable. No need to stop production.")

        st.subheader("📦 Supplier Evaluation")
        mpv = (standard_price - actual_price) * actual_quantity
        st.write(f"**Material Price Variance:** Rs. {mpv}")
        if mpv < 0:
            st.error("Unfavourable variance: consider changing suppliers or reviewing material costs.")
        else:
            st.success("Favourable variance: supplier pricing is good.")
