from diagrams import Cluster, Diagram, Edge
from diagrams.onprem.storage import Flinn
from diagrams.onprem.analytics import Spark
from diagrams.onprem.compute import Server
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.client import Users
from diagrams.gcp.analytics import BigQuery
from diagrams.gcp.devtools import Build
from diagrams.gcp.operations import Monitoring
from diagrams.onprem.workflow import Airflow

with Diagram(
    "Real-Time VN30 Pipeline (1,000 Dashboards)",
    show=False,
    direction="LR",
    filename="docs/edge_case_architecture",
):
    api = Server("SSI / Market API")

    with Cluster("Ingestion"):
        fetcher = Server("Fetcher Service")

    with Cluster("Event Bus"):
        kafka = Kafka("Kafka")

    with Cluster("Streaming Compute"):
        stream = Spark("Flink / PySpark")

    with Cluster("Storage & Modeling"):
        bq_raw = BigQuery("BigQuery (Raw)")
        bq_agg = BigQuery("BigQuery (Aggregates)")
        dbt = Build("dbt Models")

    with Cluster("Delivery"):
        cache = Redis("Cache (Hot Metrics)")
        push = Server("Push Gateway")
        users = Users("Investor Dashboards")

    orchestrator = Airflow("Airflow")
    monitoring = Monitoring("Monitoring")

    api >> fetcher >> kafka >> stream
    stream >> bq_raw
    stream >> bq_agg
    bq_raw >> dbt >> bq_agg
    bq_agg >> cache >> push >> users

    orchestrator >> Edge(style="dashed") >> [fetcher, stream, dbt]
    monitoring >> Edge(style="dotted") >> [fetcher, stream, push, bq_agg]
