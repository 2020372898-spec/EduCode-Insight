"""Assignment dashboard without the Question Analysis tab."""

from ._legacy_app_impl import (
    DEFAULT_MODEL_LABEL,
    category_counts,
    load_assignment_by_slug,
    pd,
    results_to_dataframe,
    rubric_criterion_counts,
    st,
)


def render_assignment_dashboard(
    assignment_name: str,
    assignment_slug: str,
):
    """Render one stored assignment dashboard."""
    results, meta = load_assignment_by_slug(assignment_slug)

    if not results:
        st.info("No processed student results were found for this assignment.")
        return

    df = results_to_dataframe(results)
    counts = category_counts(df)
    patterns = rubric_criterion_counts(df)

    st.subheader(assignment_name)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Students", len(results))
    c2.metric("Failed / Partial Items", len(df))
    c3.metric("AI Cost", f"${meta.get('dataset_cost_usd', 0.0):.4f}")
    c4.metric("Processing Time", f"{meta.get('elapsed_minutes', 0.0):.1f} min")

    tabs = st.tabs(
        [
            "Overview",
            "Recurring Patterns",
            "Student Details",
            "AI Usage",
        ]
    )

    with tabs[0]:
        st.markdown("#### Error Category Distribution")
        category_df = counts.rename("count").to_frame()
        st.bar_chart(category_df, use_container_width=True)
        st.dataframe(
            category_df.reset_index(names="category"),
            use_container_width=True,
            hide_index=True,
        )

    with tabs[1]:
        st.markdown("#### Most Frequent Failed / Partial Criteria")

        if patterns.empty:
            st.info("No recurring patterns were found.")
        else:
            top_patterns = patterns.head(20)
            st.bar_chart(
                top_patterns.set_index("rubric_text")[["count"]],
                use_container_width=True,
            )
            st.dataframe(
                top_patterns,
                use_container_width=True,
                hide_index=True,
            )

    with tabs[2]:
        st.markdown("#### Student Details")

        student_ids = sorted(
            {
                str(result.get("student_id", ""))
                for result in results
                if str(result.get("student_id", "")).strip()
            }
        )

        if not student_ids:
            st.info("No student identifiers were found in the stored results.")
        else:
            selected_student = st.selectbox(
                "Student",
                student_ids,
                key="assignment_student_" + assignment_slug,
            )

            student_df = (
                df[df["student_id"].astype(str) == selected_student]
                if not df.empty
                else pd.DataFrame()
            )

            if student_df.empty:
                st.info(
                    "No failed or partially met criteria were found for this student."
                )
            else:
                columns = [
                    "question_number",
                    "question_title",
                    "rubric_text",
                    "status",
                    "category",
                    "reason",
                    "justification",
                ]
                available_columns = [
                    column for column in columns if column in student_df.columns
                ]
                st.dataframe(
                    student_df[available_columns],
                    use_container_width=True,
                    hide_index=True,
                )

    with tabs[3]:
        st.markdown("#### AI Usage and Reproducibility")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "Input Tokens",
            f"{meta.get('dataset_input_tokens', 0):,}",
        )
        c2.metric(
            "Output Tokens",
            f"{meta.get('dataset_output_tokens', 0):,}",
        )
        c3.metric(
            "API Requests",
            f"{meta.get('dataset_api_requests', 0):,}",
        )
        c4.metric(
            "Model",
            meta.get("model_label", DEFAULT_MODEL_LABEL),
        )

        st.write("Prompt hash:", meta.get("prompt_hash", "Not available"))
        st.write("Prompt modified:", meta.get("prompt_modified", False))

        with st.expander("View prompt used"):
            st.code(
                meta.get("prompt_used", "Prompt not stored."),
                language="text",
            )


class AssignmentDashboardPage:
    """Owns rendering for the assignment dashboard."""

    def render(self, *args, **kwargs):
        return render_assignment_dashboard(*args, **kwargs)


__all__ = ["AssignmentDashboardPage", "render_assignment_dashboard"]
