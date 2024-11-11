import glob
import os

from graphviz import Digraph


def get_next_version():
    # Get existing diagram versions
    existing_files = glob.glob(
        "reports/figures/workflow_diagrams/mlops_workflow_v*.png"
    )
    if not existing_files:
        return 1
    versions = [int(f.split("_v")[-1].split(".")[0]) for f in existing_files]
    return max(versions) + 1


def create_mlops_workflow_v2():
    # Create a new directed graph with improved layout
    dot = Digraph(
        comment="MLOps Workflow Detailed",
        graph_attr={
            "rankdir": "TB",
            "size": "18,14!",
            "dpi": "300",
            "splines": "polyline",
            "concentrate": "true",
            "nodesep": "0.8",
            "ranksep": "1.0",
            "compound": "true",
        },
    )

    # Enhanced node styles
    dot.attr(
        "node",
        shape="box",
        style="filled,rounded",
        fontname="Helvetica",
        fontsize="14",
        height="1.4",
        width="2.2",
        margin="0.3",
    )

    # Enhanced edge styles
    dot.attr(
        "edge", fontsize="12", fontname="Helvetica", penwidth="1.8", color="#666666"
    )

    # Create clusters with improved grouping
    with dot.subgraph(name="cluster_0") as c:
        c.attr(
            label="1. CI/CD Pipeline (GitHub Actions)",
            style="filled",
            color="#E8E8E8",
            bgcolor="#F5F5F5",
            fontname="Helvetica-Bold",
            fontsize="16",
            margin="20",
        )
        c.node(
            "cron",
            "⏰\nDaily Scheduler\n- Midnight Trigger\n- Version Check\n(Step 1)",
            shape="circle",
            fillcolor="white",
        )
        c.node(
            "update_version",
            "📊\nVersion Control\n- Update Data Version\n- Log Changes\n(Step 2)",
            fillcolor="white",
        )
        c.node(
            "trigger_pipeline",
            "🚀\nPipeline Trigger\n- Start DVC Pipeline\n- Check Dependencies\n(Step 3)",
            fillcolor="white",
        )
        c.node(
            "push_main",
            "⬆️\nRepository Update\n- Push Changes\n- Update Main\n(Step 4)",
            fillcolor="white",
        )
        c.node(
            "deploy_api",
            "🔄\nDeployment\n- Rebuild Docker Image\n- Update API\n(Step 5)",
            fillcolor="white",
            xlabel="🚧",
        )

    with dot.subgraph(name="cluster_1") as c:
        c.attr(
            label="2. DVC Pipeline (MLFlow/DVC)",
            style="filled",
            color="#FFF8DC",
            bgcolor="#FFFACD",
            fontname="Helvetica-Bold",
            fontsize="16",
            margin="20",
        )
        c.node(
            "append_data",
            "📥\nData Pipeline\n- Append New Data\n- Process Updates\n(Step 6)",
            fillcolor="white",
        )
        c.node(
            "validate_data",
            "✅\nValidation\n- Schema Validation\n(Step 7)",
            fillcolor="white",
        )
        c.node(
            "transform_data",
            "⚙️\nTransformation\n- Feature Engineering\n- Data Prep\n(Step 8)",
            fillcolor="white",
        )
        c.node(
            "train_model",
            "🧠\nModel Training\n- Algorithm Update\n(Step 9)",
            fillcolor="white",
        )
        c.node(
            "evaluate_model",
            "📈\nEvaluation\n- Performance Metrics\n(Step 10)",
            fillcolor="white",
        )

    with dot.subgraph(name="cluster_2") as c:
        c.attr(
            label="3. Experiment Monitoring",
            style="filled",
            color="#E6F3FF",
            bgcolor="#F0F8FF",
            fontname="Helvetica-Bold",
            fontsize="16",
            margin="20",
        )
        c.node(
            "mlflow_registry",
            "📚\nMLFlow Registry\n- Track Experiments\n- Store Results\n(Step 11)",
            fillcolor="white",
        )
        c.node(
            "dvc_version",
            "💾\nDVC Version\n- Data Versioning\n- Model Tracking\n(Step 12)",
            fillcolor="white",
        )

    with dot.subgraph(name="cluster_3") as c:
        c.attr(
            label="4. Deployed Application",
            style="filled",
            color="#E0FFE0",
            bgcolor="#F0FFF0",
            fontname="Helvetica-Bold",
            fontsize="16",
            margin="20",
        )
        c.node(
            "new_api",
            "🌟\nAPI Service\n- New Version\n- Endpoints Update\n(Step 13)",
            fillcolor="white",
        )
        c.node(
            "user_interaction",
            "👥\nUser Interface\n- Recommendations\n- Feedback\n(Step 14)",
            fillcolor="white",
            xlabel="🚧",
        )

    with dot.subgraph(name="cluster_4") as c:
        c.attr(
            label="5. Monitoring Stack",
            style="filled",
            color="#FFE6E6",
            bgcolor="#FFF0F0",
            fontname="Helvetica-Bold",
            fontsize="16",
            margin="20",
        )
        c.node(
            "metrics",
            "📊\nMetrics\n- Performance Data\n- Usage Stats\n(Step 15)",
            fillcolor="white",
        )
        c.node(
            "dashboard",
            "📉\nDashboard\n- Visualization\n- Reporting\n(Step 16)",
            fillcolor="white",
        )
        c.node(
            "alerts",
            "⚠️\nAlerts\n- Notifications\n- Incidents\n(Step 17)",
            fillcolor="white",
            xlabel="🚧",
        )

    # Define detailed edges with improved descriptions
    edges = [
        (
            "cron",
            "update_version",
            "1️⃣ Schedule → Version\n- Daily Trigger\n- Version Check",
        ),
        (
            "update_version",
            "trigger_pipeline",
            "2️⃣ Version → Pipeline\n- Start Process\n- Validate",
        ),
        ("trigger_pipeline", "append_data", "3️⃣ Pipeline → Data\n- Process New Data"),
        ("append_data", "validate_data", "4️⃣ Data → Validation\n- Schema Check"),
        ("validate_data", "transform_data", "5️⃣ Validate → Transform\n- Feature Prep"),
        ("transform_data", "train_model", "6️⃣ Transform → Train\n- Model Update"),
        ("train_model", "evaluate_model", "7️⃣ Train → Evaluate\n- Performance"),
        ("evaluate_model", "mlflow_registry", "8️⃣ Evaluate → Log\n- Track Results"),
        ("evaluate_model", "dvc_version", "9️⃣ Evaluate → Version\n- Save State"),
        ("evaluate_model", "push_main", "🔟 Evaluate → Push\n- Update Repo"),
        ("push_main", "deploy_api", "1️⃣1️⃣ Push → Deploy\n- Service Update"),
        ("deploy_api", "new_api", "1️⃣2️⃣ Deploy → API\n- New Version"),
        ("new_api", "user_interaction", "1️⃣3️⃣ API → Users\n- Serve"),
        ("user_interaction", "metrics", "1️⃣4️⃣ Users → Metrics\n- Track"),
        ("metrics", "dashboard", "1️⃣5️⃣ Metrics → Display\n- Visualize"),
        ("metrics", "alerts", "1️⃣6️⃣ Metrics → Alerts\n- Monitor"),
    ]

    # Add edges with improved styling
    for src, dst, label in edges:
        dot.edge(
            src,
            dst,
            label,
            minlen="2",
            fontsize="11",
            labelangle="45",
            labeldistance="2.0",
        )

    # Add enhanced legend
    with dot.subgraph(name="cluster_legend") as legend:
        legend.attr(
            label="🔍 Pipeline Components & Flow",
            style="filled",
            color="white",
            fontsize="16",
        )
        legend.node(
            "l1",
            "🔄 CI/CD Pipeline\nAutomated Deployment",
            style="filled",
            fillcolor="#F5F5F5",
        )
        legend.node(
            "l2",
            "📊 Data Pipeline\nProcessing & Training",
            style="filled",
            fillcolor="#FFFACD",
        )
        legend.node(
            "l3", "🚀 API Service\nUser Interface", style="filled", fillcolor="#F0FFF0"
        )
        legend.node(
            "l4", "📈 Monitoring\nMetrics & Alerts", style="filled", fillcolor="#FFF0F0"
        )

    return dot


if __name__ == "__main__":
    try:
        # Create versioned output directory
        os.makedirs("reports/figures/workflow_diagrams", exist_ok=True)

        # Get next version number
        version = get_next_version()

        # Create the workflow diagram
        workflow = create_mlops_workflow_v2()

        # Generate versioned output files
        output_base = f"reports/figures/workflow_diagrams/mlops_workflow_v{version}"

        # Generate PNG with timestamp
        workflow.render(output_base, format="png", cleanup=True)
        print(f"✅ PNG diagram v{version} generated: {output_base}.png")

        # Generate SVG with timestamp
        workflow.render(output_base, format="svg", cleanup=True)
        print(f"✅ SVG diagram v{version} generated: {output_base}.svg")

        # Create a latest copy
        import shutil

        shutil.copy(
            f"{output_base}.png",
            "reports/figures/workflow_diagrams/mlops_workflow_latest.png",
        )
        shutil.copy(
            f"{output_base}.svg",
            "reports/figures/workflow_diagrams/mlops_workflow_latest.svg",
        )

        print(f"\n✨ New version {version} created successfully!")
        print("\nDiagram Components:")
        print("⏰ Scheduler  : Automated timing and triggers")
        print("📊 Version    : Data and code versioning")
        print("🚀 Pipeline   : Automated workflow execution")
        print("🧠 Training   : Model development and updates")
        print("📈 Analytics  : Performance monitoring")
        print("🌟 Service    : API and deployment")
        print("👥 Users      : Interaction handling")
        print("⚠️ Monitoring : System health and alerts")

    except Exception as e:
        print(f"❌ Error generating diagram: {str(e)}")
