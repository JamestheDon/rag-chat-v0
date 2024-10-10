from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core import ChatPromptTemplate

"""
Sample prompts for generating enrichments from context:

KEY_INFO_EXTRACTOR_TMPL = "
    Extract all critical details from the following invoice, 
    including invoice number, 
    date, 
    vendor information, 
    purchaser details, 
    line items with descriptions, 
    quantities, 
    unit prices, 
    subtotals, 
    taxes, 
    discounts, 
    total amount due, 
    payment terms, 
    and due date.
    "

ANOMALY_DETECTOR_TMPL = "
    Analyze the following invoice for any discrepancies or anomalies, 
    such as mismatched totals, 
    missing line items, 
    incorrect calculations, 
    unusual payment terms, 
    or inconsistent vendor information.
    "
COMPLIANCE_CHECKER_TMPL = "
    Verify that the following invoice complies with 
    standard accounting practices and regulatory requirements, 
    noting any missing mandatory information or formatting issues.
    "
RISK_ASSESSMENT_TMPL = "
    Assess the risk associated with processing the following invoice 
    by evaluating factors like unfamiliar vendors, 
    unusually high amounts, 
    changes in banking details, 
    or inconsistent billing patterns.
    "
DATA_VALIDATION_TMPL = "
    Validate the accuracy of the data presented in the following invoice, 
    ensuring all calculations are correct and all required fields are populated accurately.
    "
FRAUD_DETECTION_TMPL = "
    Evaluate the following invoice for potential signs of fraud, 
    including duplicate invoice numbers, 
    altered vendor information, 
    discrepancies in line item details, 
    or unauthorized changes in payment instructions.
    "
EXPENSE_CATEGORIZATION_TMPL = "
    Categorize each line item in the following invoice into 
    standard accounting categories based on the descriptions provided, 
    such as 'Office Supplies,' 'Consulting Services,' or 'Software Licenses.'
    "
PAYMENT_TERMS_ANALYSIS_TMPL = "
    Extract and interpret the payment terms from the following invoice, 
    including due dates, 
    early payment discounts, 
    and late payment penalties.
    "
HISTORICAL_COMPARISON_TMPL = "
    Compare the details of the following invoice with past invoices 
    from the same vendor to identify any significant deviations 
    in pricing, quantities, or terms.
    "
"""

DEFAULT_QUESTION_GEN_TMPL = """\
Here is the context:
{context_str}

Given the contextual information, \
generate {num_questions} questions this context can provide \
specific answers to which are unlikely to be found elsewhere.

Higher-level summaries of surrounding context may be provided \
as well. Try using these summaries to generate better questions \
that this context can answer.

"""
COMPLIANCE_CHECKER_TMPL = """\
Here is the context:
{context_str}

Given the contextual information, \
verify that the following invoice complies with \
standard accounting practices and regulatory requirements, \
noting any missing mandatory information or formatting issues.
"""

"""   
# text qa prompt
COMPLIANCE_CHECKER_SYSTEM_PROMPT = ChatMessage(
    content=(
        "You are a highly knowledgeable compliance officer specializing in financial regulations, accounting standards, and invoice auditing.\n"
        "Always perform your analysis using only the provided context information, and do not rely on prior knowledge.\n"
        "Some rules to follow:\n"
        "1. Never directly reference the given context in your analysis.\n"
        "2. Avoid statements like 'Based on the context, ...' or 'The context information ...' or anything along those lines.\n"
        "3. Provide clear, concise, and professional responses focusing on compliance-related issues."
    ),
    role=MessageRole.SYSTEM,
)

COMPLIANCE_CHECKER_PROMPT_TMPL_MSGS = [
    COMPLIANCE_CHECKER_SYSTEM_PROMPT,
    ChatMessage(
        content=(
            "Context information is below.\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "Given the context information and not prior knowledge, \
            verify that the following invoice complies with \
            standard accounting practices and regulatory requirements, \
            noting any missing mandatory information or formatting issues.\n"
            "Query: {query_str}\n"
            "Answer: "
        ),
        role=MessageRole.USER,
    ),
]

CHAT_COMPLIANCE_CHECKER_PROMPT = ChatPromptTemplate(message_templates=COMPLIANCE_CHECKER_PROMPT_TMPL_MSGS)
"""