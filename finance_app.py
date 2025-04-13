import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import os

st.set_page_config(page_title="Finance Report", layout="centered")
st.title("📊 Finance Report Generator")

# Input: Company Details
st.header("Company Details")
company_name = st.text_input("Enter Company's Name")
n = st.number_input("Enter number of products", min_value=1, step=1)
FC = st.number_input("Enter total fixed cost", min_value=0)

# Session state init
if "report_generated" not in st.session_state:
    st.session_state.report_generated = False

if company_name and n:
    with st.form("finance_form"):
        Names, Sales, VC = [], [], []
        for i in range(int(n)):
            st.markdown(f"**Product {i+1}**")
            name = st.text_input(f"Name", key=f"name_{i}")
            sale = st.number_input(f"Selling Price", min_value=0, key=f"sale_{i}")
            vc = st.number_input(f"Variable Cost", min_value=0, key=f"vc_{i}")
            Names.append(name)
            Sales.append(sale)
            VC.append(vc)

        st.subheader("Supplier Evaluation")
        std_price = st.number_input("Standard Material Price", min_value=0)
        act_price = st.number_input("Actual Material Price", min_value=0)
        act_qty = st.number_input("Actual Quantity", min_value=0)

        submitted = st.form_submit_button("Generate Report")

    if submitted:
        # Calculations
        df = pd.DataFrame({"Name": Names, "Sales": Sales, "VC": VC})
        df["Contribution"] = df["Sales"] - df["VC"]
        df["PV_ratio/unit"] = df.apply(lambda row: ((row["Sales"] - row["VC"]) / row["Sales"] * 100)
                                       if row["Sales"] > 0 else 0, axis=1)

        total_sales = df["Sales"].sum()
        total_vc = df["VC"].sum()
        net_profit = total_sales - (FC + total_vc)
        PV_ratio = ((total_sales - total_vc) / total_sales) * 100 if total_sales > 0 else 0
        BEP = FC / (PV_ratio / 100) if PV_ratio > 0 else 0
        stop_list = df[df["Contribution"] <= 0]["Name"].tolist()
        pv_max = df.loc[df["PV_ratio/unit"].idxmax()]["Name"]
        pv_min = df.loc[df["PV_ratio/unit"].idxmin()]["Name"]
        mpv = (std_price - act_price) * act_qty
        mpv_msg = ("It is favourable. The price of material you are buying is good w.r.t. the market price"
                   if mpv >= 0 else
                   "It is unfavourable. This means the company needs to change the supplier or need to make materials instead of buying")

        # Save chart image
        fig, ax = plt.subplots()
        ax.bar(df["Name"], df["PV_ratio/unit"], color='red')
        ax.set_title("Product Name vs PV ratio / unit")
        ax.set_xlabel("Product Name")
        ax.set_ylabel("PV ratio / unit")
        chart_file = "pvratio_bar_chart.png"
        fig.savefig(chart_file)
        st.pyplot(fig)

        # Compose all report content as text blocks (for web + PDF)
        st.subheader("📄 Full Report View (Same as PDF)")

        text = f"""
### 📘 Company's Details :-
- Company Name : {company_name}
- Total number of Products : {int(n)}
- Fixed Cost : {FC}
- Total Sales : {total_sales}
- Net Profit : {net_profit}

---

### ❗ Need to stop production of any product?
{"- Every product is running in profit. No need to stop production of any product." if not stop_list else "- Stop production of: " + ", ".join(stop_list)}

---

### 📊 Product Contribution in making profit :-
- Here is a bar graph comparing PV ratio of every product.
- Highest contributor: **{pv_max}**
- Least contributor: **{pv_min}**

---

### 🧮 Break Even Point :-
- BEP = Rs.{round(BEP, 2)}
- It is amount where the comapny covers its cost and can generate profit after selling every product.

---

### 🧾 Is your supplier beneficial for the company?
- Material price variance = Rs.{mpv}
- {mpv_msg}
"""
        st.markdown(text)

        # Generate PDF with the same content
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 18)
        pdf.cell(200, 10, "Finance Report", ln=True, align='C')

        pdf.set_font("Arial", size=12)
        pdf.ln(5)
        pdf.multi_cell(0, 10, "Company's Details :-")
        pdf.multi_cell(0, 10, f"Company Name : {company_name}")
        pdf.multi_cell(0, 10, f"Total number of Products : {int(n)}")
        pdf.multi_cell(0, 10, f"Fixed Cost : {FC}")
        pdf.multi_cell(0, 10, f"Total Sales : {total_sales}")
        pdf.multi_cell(0, 10, f"Net Profit : {net_profit}")
        pdf.multi_cell(0, 10, " ")

        pdf.multi_cell(0, 10, "Need to stop production of any product ?")
        if stop_list:
            pdf.multi_cell(0, 10, f"Since Contribution<=0 for this products list {', '.join(stop_list)}, the company need to immediately stop the production of this, because it is indirectly creating loss.")
        else:
            pdf.multi_cell(0, 10, "Every product is running in profit. No need to stop production of any product.")
        pdf.multi_cell(0, 10, " ")

        pdf.multi_cell(0, 10, "Product Contribution in making profit :-")
        pdf.multi_cell(0, 10, "Here is a bar graph comparing PV ratio of every product -----")
        pdf.image(chart_file, w=190)
        pdf.multi_cell(0, 10, f"This graph indicates that {pv_max} is the highest contributer in the company's overall profit.")
        pdf.multi_cell(0, 10, f"And {pv_min} is the least contributer in the company's overall profit.")
        pdf.multi_cell(0, 10, " ")

        pdf.multi_cell(0, 10, "Break Even Point :-")
        pdf.multi_cell(0, 10, f"BEP = Rs.{round(BEP, 2)}")
        pdf.multi_cell(0, 10, "It is amount where the comapny covers its cost and can generate profit after selling every product.")
        pdf.multi_cell(0, 10, " ")

        pdf.multi_cell(0, 10, "Is your supplier beneficial for the company ?")
        pdf.multi_cell(0, 10, f"Material price variance = {mpv}")
        pdf.multi_cell(0, 10, mpv_msg)

        pdf_bytes = pdf.output(dest="S").encode("latin1")
        st.download_button("📥 Download PDF Report", data=pdf_bytes, file_name="Finance_Report.pdf", mime="application/pdf")

        if os.path.exists(chart_file):
            os.remove(chart_file)

        st.session_state.report_generated = True
