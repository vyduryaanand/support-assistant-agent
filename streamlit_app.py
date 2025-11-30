# streamlit_app.py
"""
Support Assistant Agent:
Resolve predefined FAQs first; escalate complex queries to AI.

Features:
- Check question against predefined FAQs
- If matched → return predefined answer
- If not matched → call OpenRouter API
- Store answered FAQs locally (session_state)
- Display 10 recent FAQs
"""

import os
import string
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI

# -------------------------------------------------------
# PRIORITY: 1) Streamlit Secrets  2) .env  3) Defaults
# -------------------------------------------------------
load_dotenv()  # enables local development

def get_secret(key: str, default=None):
    """Load from Streamlit secrets → .env → default."""
    if key in st.secrets:
        return st.secrets[key]
    return os.getenv(key, default)

OPENROUTER_API_KEY = get_secret("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = get_secret("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = get_secret("OPENROUTER_MODEL", "openai/gpt-oss-20b:free")

if not OPENROUTER_API_KEY:
    st.error("Missing OPENROUTER_API_KEY. Add it to Streamlit Secrets or .env.")
    st.stop()

# -------------------------------------------------------
# OpenRouter Client
# -------------------------------------------------------
client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY
)

# -------------------------------------------------------
# Predefined FAQs (Your full knowledge base)
# -------------------------------------------------------
PREDEFINED_FAQS = {
    # ------------------ GENERAL SUPPORT ------------------
    "how to reset password":
        "To reset your password, click the 'Forgot Password' link on the login page and follow the instructions.",

    "how to contact support":
        "You can contact support anytime at support@example.com or through the in-app Help Center.",

    "what is your refund policy":
        "We offer a 7-day refund policy for all subscription plans. Contact billing@example.com to request a refund.",

    "how to change my email":
        "You can change your registered email from Settings → Account → Update Email.",

    "how to update my profile":
        "Go to Settings → Profile to update your personal or business details.",

    "how to cancel subscription":
        "You can cancel your subscription anytime from Billing → Manage Subscription.",

    "do you offer customer support":
        "Yes, we offer 24/7 customer support through email and chat.",

    "what payment methods do you accept":
        "We accept Visa, MasterCard, American Express, UPI, and PayPal.",

    "how long does customer support take to respond":
        "Our support team typically replies within 2 hours.",

    "do you offer onboarding assistance":
        "Yes, our onboarding team can assist new users with setup and configuration.",

    # ------------------ SALES FAQs ------------------
    "do you offer demo":
        "Yes, you can request a live product demo by contacting sales@example.com.",

    "what are your pricing plans":
        "We offer Basic, Pro, and Enterprise plans. Visit our Pricing page for details.",

    "do you offer discounts":
        "Yes, we offer annual subscription discounts and volume-based pricing for teams.",

    "how to contact sales team":
        "You can contact our sales team at sales@example.com or schedule a call via our website.",

    "do you have enterprise plans":
        "Yes, we provide customized enterprise solutions with dedicated account managers.",

    "is bulk purchasing available":
        "Bulk licenses are available with special pricing. Contact sales@example.com for a quote.",

    "do you offer free trial":
        "Yes, we offer a 14-day free trial with full feature access.",

    "what features are included in premium plan":
        "Premium includes analytics dashboard, automation tools, unlimited users, and priority support.",

    "how to upgrade plan":
        "You can upgrade your plan in Billing → Subscription → Upgrade.",

    # ------------------ MARKETING FAQs ------------------
    "what marketing tools do you provide":
        "We offer email automation, campaign tracking, lead scoring, and CRM integration.",

    "does your platform support email marketing":
        "Yes, you can send campaigns, automate workflows, and track open/click rates.",

    "do you provide analytics":
        "Yes, we provide detailed analytics on customer engagement, conversion rates, and traffic.",

    "can i track leads":
        "Yes, our lead tracking system helps you monitor lead sources and conversion progress.",

    "do you integrate with crm systems":
        "We integrate with Salesforce, HubSpot, Zoho, and other major CRM platforms.",

    "do you offer social media automation":
        "Yes, you can schedule posts and track performance across major social media channels.",

    "can i export marketing reports":
        "Yes, reports can be exported in PDF, CSV, and Excel formats.",

    "do you support a b testing":
        "Yes, A/B testing is available for email campaigns and landing pages.",

    # ------------------ PRODUCT SUPPORT ------------------
    "is my data secure":
        "Yes, we follow industry-standard encryption and security practices to protect your data.",

    "how often is the system updated":
        "System updates occur weekly with improvements, bug fixes, and new features.",

    "does your platform support mobile":
        "Yes, our platform is mobile-responsive and works on all major devices.",

    "what browsers do you support":
        "We support Chrome, Firefox, Safari, and Edge.",

    "how to report a bug":
        "You can report bugs through Help Center → Report Issue.",

    "is training available":
        "Yes, we provide free training videos and paid personalized training sessions.",

    # ------------------ ACCOUNT / BILLING ------------------
    "where can i download invoices":
        "Invoices are available under Billing → Payment History.",

    "why was my payment declined":
        "Payments may fail due to insufficient balance or verification issues. Contact your bank or try again.",

    "can i add multiple team members":
        "Yes, go to Settings → Team Management to add or remove users.",

    "can i change my billing cycle":
        "Yes, you can switch between monthly and yearly billing under Subscription Settings.",

    # ------------------ ORDER / DELIVERY ------------------
    "how do i track my order":
        "You can track your order using the tracking link sent to your registered email.",

    "do you ship internationally":
        "Yes, we ship to over 40+ countries. Shipping charges may apply.",
}

# -------------------------------------------------------
# Helper functions
# -------------------------------------------------------

def clean(text: str):
    """Normalize text for matching."""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text.strip()

def find_faq_answer(user_question: str):
    """Return predefined FAQ answer if similar enough."""
    cleaned_q = clean(user_question)

    for faq_question, faq_answer in PREDEFINED_FAQS.items():
        cleaned_faq = clean(faq_question)

        # Basic exact/substring check
        if cleaned_faq in cleaned_q or cleaned_q in cleaned_faq:
            return faq_answer

        # Partial word overlap
        common = set(cleaned_q.split()) & set(cleaned_faq.split())
        score = len(common) / max(len(cleaned_faq.split()), 1)

        if score >= 0.6:
            return faq_answer

    return None


def generate_ai_answer(question: str):
    """Escalate query to AI model."""
    try:
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[{"role": "user", "content": question}],
            extra_body={"reasoning": {"enabled": True}}
        )

        msg = response.choices[0].message
        return msg.get("content") if isinstance(msg, dict) else msg.content

    except Exception as e:
        st.error(f"OpenRouter API Error: {e}")
        return None


# -------------------------------------------------------
# Streamlit UI
# -------------------------------------------------------

st.set_page_config(page_title="Support Assistant Agent")
st.title("Support Assistant Agent")
st.write("Smart FAQ resolver — escalates complex queries to AI.")

if "faqs" not in st.session_state:
    st.session_state.faqs = []

with st.form("ask_form"):
    user_question = st.text_area("Ask your question:")
    ask_btn = st.form_submit_button("Submit")

if ask_btn:
    if not user_question.strip():
        st.warning("Please enter a question.")
    else:
        predefined_answer = find_faq_answer(user_question)

        if predefined_answer:
            st.success("Answered from FAQ database (no AI used).")
            answer = predefined_answer
        else:
            st.info("Escalating to AI...")
            with st.spinner("Thinking..."):
                answer = generate_ai_answer(user_question)

        st.subheader("Answer")
        st.write(answer)

        st.session_state.faqs.append({
            "time": datetime.utcnow().isoformat(),
            "question": user_question,
            "answer": answer
        })

# -------------------------------------------------------
# Recent FAQs
# -------------------------------------------------------
st.markdown("---")
st.header("Recent FAQs (local memory)")

if not st.session_state.faqs:
    st.info("No FAQs yet.")
else:
    for item in reversed(st.session_state.faqs[-10:]):
        st.markdown(f"**Q:** {item['question']}")
        st.markdown(f"**A:** {item['answer']}")
        st.caption(f"Time (UTC): {item['time']}")
        st.markdown("---")