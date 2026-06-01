from graph import graph

# Get topic from user
query = input("\nEnter research topic: ")

# Run LangGraph workflow
result = graph.invoke(
    {
        "query": query
    }
)

# Display report
print("\n=== REPORT ===\n")
print(result["formatted_report"])

# Save report
with open(
    "reports/latest_report.md",
    "w",
    encoding="utf-8"
) as f:
    f.write(
        result["formatted_report"]
    )

print("\nReport saved to reports/latest_report.md")