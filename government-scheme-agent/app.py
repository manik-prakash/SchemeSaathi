from __future__ import annotations

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from agent.agent_executor import run_agent
from agent.memory import load_memory, save_memory
from models.schemas import UserProfile


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

TOOL_ICONS = {
    'scheme_finder': '🔍',
    'eligibility_checker': '✅',
    'calculator': '📊',
    'web_search': '🌐',
    'session_context': '👤',
}

CSS = """
<style>
/* Hero banner */
.hero {
    background: linear-gradient(135deg, #1a3c6e 0%, #2d6a9f 100%);
    padding: 1.5rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    color: white;
}
.hero h1 { color: white; font-size: 1.9rem; margin: 0 0 0.3rem 0; }
.hero p  { color: #c8dff5; margin: 0; font-size: 0.95rem; }

/* Verdict badges */
.badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-weight: 600;
    font-size: 0.85rem;
    margin-left: 0.4rem;
}
.badge-green  { background: #d1fae5; color: #065f46; }
.badge-amber  { background: #fef3c7; color: #92400e; }
.badge-red    { background: #fee2e2; color: #991b1b; }

/* Confidence bar */
.conf-wrap { margin: 0.5rem 0 0.75rem; }
.conf-label { font-size: 0.8rem; color: #6b7280; margin-bottom: 3px; }
.conf-bar-bg { background: #e5e7eb; border-radius: 999px; height: 10px; }
.conf-bar-fill { border-radius: 999px; height: 10px; }
.conf-green { background: #10b981; }
.conf-amber { background: #f59e0b; }
.conf-red   { background: #ef4444; }

/* Scheme card name */
.scheme-name { font-size: 1.15rem; font-weight: 700; margin-bottom: 0.25rem; }

/* Condition bullets */
.cond-list { list-style: none; padding: 0; margin: 0.2rem 0 0.5rem; }
.cond-list li { font-size: 0.9rem; padding: 1px 0; }

/* Apply link */
.apply-link a { font-weight: 600; color: #2563eb; }

/* Footer disclaimer */
.disclaimer {
    background: #f9fafb;
    border-left: 4px solid #d1d5db;
    padding: 0.6rem 1rem;
    border-radius: 4px;
    color: #6b7280;
    font-size: 0.82rem;
    margin-top: 1rem;
}

/* Section label */
.section-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #9ca3af;
    margin: 1rem 0 0.3rem;
}
</style>
"""


def build_profile_from_form() -> UserProfile:
    return UserProfile(
        age=st.session_state.age,
        gender=st.session_state.gender,
        state=st.session_state.state,
        student_status=st.session_state.student_status,
        annual_family_income=st.session_state.annual_family_income,
        category=st.session_state.category,
        disability_status=st.session_state.disability_status,
        education_level=st.session_state.education_level,
        occupation=st.session_state.occupation,
        area_type=st.session_state.area_type,
    )


def verdict_badge(verdict: str) -> str:
    if verdict.startswith('Clearly'):
        cls = 'badge-green'
    elif verdict.startswith('Maybe'):
        cls = 'badge-amber'
    else:
        cls = 'badge-red'
    return f'<span class="badge {cls}">{verdict}</span>'


def confidence_bar(conf: float) -> str:
    pct = int(conf * 100)
    if conf >= 0.7:
        color = 'conf-green'
    elif conf >= 0.4:
        color = 'conf-amber'
    else:
        color = 'conf-red'
    return (
        f'<div class="conf-wrap">'
        f'<div class="conf-label">Confidence: {pct}%</div>'
        f'<div class="conf-bar-bg"><div class="conf-bar-fill {color}" style="width:{pct}%"></div></div>'
        f'</div>'
    )


def render_results(results):
    st.subheader('Eligibility Results')
    if not results:
        st.warning('No schemes matched this profile strongly. Try adjusting the profile or adding more details.')
        return

    for item in results:
        with st.container(border=True):
            st.markdown(
                f'<div class="scheme-name">{item.scheme_name} {verdict_badge(item.verdict)}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(confidence_bar(item.confidence), unsafe_allow_html=True)
            st.markdown(f'**Reason:** {item.reason}')

            if item.benefits:
                with st.expander('What you get'):
                    st.write(item.benefits)

            col_a, col_b = st.columns(2)
            with col_a:
                if item.matched_conditions:
                    bullets = ''.join(f'<li>✅ {c}</li>' for c in item.matched_conditions)
                    st.markdown(
                        f'<div class="section-label">Matched</div><ul class="cond-list">{bullets}</ul>',
                        unsafe_allow_html=True,
                    )
            with col_b:
                if item.failed_conditions:
                    bullets = ''.join(f'<li>❌ {c}</li>' for c in item.failed_conditions)
                    st.markdown(
                        f'<div class="section-label">Not Met</div><ul class="cond-list">{bullets}</ul>',
                        unsafe_allow_html=True,
                    )

            if item.required_documents:
                docs = ''.join(f'<li>📄 {d}</li>' for d in item.required_documents)
                st.markdown(
                    f'<div class="section-label">Required Documents</div><ul class="cond-list">{docs}</ul>',
                    unsafe_allow_html=True,
                )

            st.markdown(
                f'<div class="apply-link"><a href="{item.official_link}" target="_blank">Apply Here →</a></div>',
                unsafe_allow_html=True,
            )


def render_trace(trace_steps):
    st.subheader('Agent Trace')
    if not trace_steps:
        st.info('No trace steps available yet.')
        return

    for step in trace_steps:
        icon = TOOL_ICONS.get(step.tool_name, '⚙️')
        label = f'{icon} Step {step.step_number}: {step.action}'
        with st.expander(label, expanded=False):
            st.markdown(f'**Tool:** `{step.tool_name}`')
            st.markdown(f'**Observation:** {step.observation}')
            if step.tool_input:
                st.json(step.tool_input)


def main():
    st.set_page_config(page_title='Government Scheme Eligibility Agent', page_icon='🏛️', layout='wide')
    st.markdown(CSS, unsafe_allow_html=True)

    st.markdown(
        '<div class="hero">'
        '<h1>🏛️ Government Scheme Eligibility Agent</h1>'
        '<p>An LLM-powered, tool-using assistant for informational government scheme eligibility screening.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    memory = load_memory(st.session_state)

    with st.sidebar:
        st.header('About')
        st.write('Uses **40+ local scheme records**, deterministic eligibility checks, and OpenRouter-backed LLM reasoning.')
        st.write('For educational and informational use only.')
        if memory.last_profile:
            st.info('✅ Previous profile loaded from session memory.')
        st.markdown('---')
        st.caption('Recommended Python: `3.10` or `3.11`')

    col1, col2 = st.columns([1, 1], gap='large')

    with col1:
        st.subheader('Your Profile')

        st.markdown('<div class="section-label">Personal Details</div>', unsafe_allow_html=True)
        st.number_input('Age', min_value=0, max_value=120, value=19, key='age')
        st.selectbox('Gender', ['Any', 'Male', 'Female', 'Other'], key='gender')
        st.selectbox('State', ['All', 'Karnataka', 'Maharashtra', 'Delhi', 'Tamil Nadu'], key='state')
        st.selectbox('Area Type', ['Rural', 'Urban'], key='area_type')

        st.markdown('<div class="section-label">Education & Occupation</div>', unsafe_allow_html=True)
        st.selectbox('Student Status', ['Yes', 'No'], key='student_status')
        st.selectbox('Education Level', ['School', 'Post-Matric', 'Undergraduate', 'Postgraduate', 'Graduate'], key='education_level')
        st.selectbox('Occupation', ['Student', 'Farmer', 'Self-Employed', 'Unemployed', 'Employed'], key='occupation')

        st.markdown('<div class="section-label">Financial & Social</div>', unsafe_allow_html=True)
        st.number_input('Annual Family Income (INR) ℹ️', min_value=0, max_value=5000000, value=200000, step=10000, key='annual_family_income')
        st.selectbox('Category', ['General', 'OBC', 'SC', 'ST', 'Minority'], key='category')
        st.selectbox('Disability Status', ['No', 'Yes'], key='disability_status')

        st.markdown('<div class="section-label">Optional</div>', unsafe_allow_html=True)
        follow_up = st.text_area('Refinement hint', placeholder='Example: prioritize scholarship schemes only')

        if st.button('Check My Eligibility', type='primary', use_container_width=True):
            profile = build_profile_from_form()
            with st.spinner('Running eligibility checks...'):
                agent_output = run_agent(profile=profile, follow_up=follow_up.strip() or None, memory=memory)
            save_memory(st.session_state, profile=profile, output=agent_output)
            st.session_state['latest_output'] = agent_output

    with col2:
        output = st.session_state.get('latest_output')
        if output:
            st.subheader('Summary')
            st.write(output.final_answer)
            render_results(output.results)
            render_trace(output.trace_steps)
        else:
            st.info('Submit your profile on the left to check eligibility.')

    st.markdown(
        '<div class="disclaimer">⚠️ <strong>Disclaimer:</strong> This system provides an informational estimate only. '
        'Final eligibility depends on official government rules and verification.</div>',
        unsafe_allow_html=True,
    )


if __name__ == '__main__':
    main()
