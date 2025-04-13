import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import os

st.title("📊 Finance Report Generator")

# Company details input
st.header("Company Details")
company_name = st.text_input("Enter Company's Name")
n = st.number_input("Enter number of products", min_value=1, step=1)
FC = st.number_input("Enter total fixed cost", min_value=0)

# Initialize session state
if "report_generated" not in st.session_state:
    st.session_state.report_generated = False
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

if company_name and n:
    with st.form("finance_form"):
        st.subheader("Enter Product Details")
        Names, Sales, VC = [], [], []
        for i in range(int(n)):
            st.markdown(f"**Product {i+1} Details**")
            name = st.text_input(f"Product {i+1} Name", key=f"name_{i}")
            sale = st.number_input(f"Selling Price of {name}", min_value=0, key=f"sale_{i}")
            vc = st.number_input(f"Variable Cost of {name}", min_value=0, key=f"vc_{i}")
            Names.append(name)
            Sales.append(sale)
            VC.append(vc)

        st.subheader("Supplier Evaluation")
        standard_price = st.number_input("Standard Material Price", min_value=0)
        actual_price = st.number_input("Actual Material Price", min_value=0)
        actual_quantity = st.number_input("Actual Quantity Purchased", min_value=0)

        submit = st.form_submit_button("Generate Report")

    if submit:
        df = pd.DataFrame({"Name": Names, "Sales": Sales, "VC": VC})
        df["Contribution"] = df["Sales"] - df["VC"]
        df["PV_ratio/unit"] = df.apply(lambda row: ((row["Sales"] - row["VC"]) / row["Sales"]) * 100 if row["Sales"] > 0 else 0, axis=1)

        Total_sales = df["Sales"].sum()
        Total_vc = df["VC"].sum()
        PV_ratio = ((Total_sales - Total_vc) / Total_sales) * 100 if Total_sales > 0 else 0
        BEP = FC / (PV_ratio / 100) if PV_ratio > 0 else 0
        net_profit = Total_sales - (FC + Total_vc)

        # Store values in session
        st.session_state.df = df
        st.session_state.company_name = company_name
        st.session_state.FC = FC
        st.session_state.Total_sales = Total_sales
        st.session_state.net_profit = net_profit
        st.session_state.BEP = BEP
        st.session_state.stop_production = df[df["Contribution"] <= 0]["Name"].tolist()
        st.session_state.max_contributor = df.loc[df["PV_ratio/unit"].idxmax()]["Name"]
        st.session_state.min_contributor = df.loc[df["PV_ratio/unit"].idxmin()]["Name"]
        st.session_state.mpv = (standard_price - actual_price) * actual_quantity
        st.session_state.mpv_msg = (
            "It is favourable. The price of material you are buying is good w.r.t. the market price"
            if st.session_state.mpv >= 0
            else "It is unfavourable. This means the company needs to change the supplier or need to make materials instead of buying"
        )

        # Save chart
        fig, ax = plt.subplots()
        ax.bar(df["Name"], df["PV_ratio/unit"], color='red')
        ax.set_title("Product Name vs PV ratio / unit")
        ax.set_xlabel("Product Name")
        ax.set_ylabel("PV ratio / unit")
        chart_file = "pvratio_bar_chart.png"
        fig.savefig(chart_file)
        st.pyplot(fig)

        # Generate PDF with matching structure
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 18)
        pdf.cell(200, 10, txt="Finance Report", ln=True, align='C')

        pdf.set_font("Arial", size=12)
        pdf.ln(5)
        pdf.multi_cell(0, 10, "Company's Details :-")
        pdf.multi_cell(0, 10, f"Company Name : {company_name}")
        pdf.multi_cell(0, 10, f"Total number of Products : {int(n)}")
        pdf.multi_cell(0, 10, f"Fixed Cost : {FC}")
        pdf.multi_cell(0, 10, f"Total Sales : {Total_sales}")
        pdf.multi_cell(0, 10, f"Net Profit : {net_profit}")
        pdf.multi_cell(0, 10, " ")

        pdf.multi_cell(0, 10, "Need to stop production of any product ?")
        if st.session_state.stop_production:
            products_str = ", ".join(st.session_state.stop_production)
            pdf.multi_cell(0, 10, f"Since Contribution<=0 for this products list {products_str}, the company need to immediately stop the production of this, because it is indirectly creating loss.")
        else:
            pdf.multi_cell(0, 10, "Every product is running in profit. No need to stop production of any product.")
        pdf.multi_cell(0, 10, " ")

        pdf.multi_cell(0, 10, "Product Contribution in making profit :-")
        pdf.multi_cell(0, 10, "Here is a bar graph comparing PV ratio of every product -----")
        pdf.image(chart_file, w=190)
        pdf.multi_cell(0, 10, f"This graph indicates that {st.session_state.max_contributor} is the highest contributer in the company's overall profit.")
        pdf.multi_cell(0, 10, f"And {st.session_state.min_contributor} is the least contributer in the company's overall profit.")
        pdf.multi_cell(0, 10, " ")

        pdf.multi_cell(0, 10, "Break Even Point :-")
        pdf.multi_cell(0, 10, f"BEP = Rs.{st.session_state.BEP}")
        pdf.multi_cell(0, 10, "It is amount where the comapny covers its cost and can generate profit after selling every product.")
        pdf.multi_cell(0, 10, " ")

        pdf.multi_cell(0, 10, "Is your supplier beneficial for the company ?")
        pdf.multi_cell(0, 10, f"Material price variance = {st.session_state.mpv}")
        pdf.multi_cell(0, 10, st.session_state.mpv_msg)

        pdf_bytes = pdf.output(dest="S").encode("latin1")
        st.session_state.pdf_bytes = pdf_bytes
        st.session_state.report_generated = True

        if os.path.exists(chart_file):
            os.remove(chart_file)

if st.session_state.report_generated and st.session_state.pdf_bytes:
    st.download_button(
        label="Download PDF Report",
        data=st.session_state.pdf_bytes,
        file_name="Finance_Report.pdf",
        mime="application/pdf"
    )
