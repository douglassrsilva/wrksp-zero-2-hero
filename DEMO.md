# Demo

Caso anónimo: calidad de red, clientes y productos de una empresa móvil chilena
ficticia. El recorrido usa once fuentes relacionadas, gobernadas por Unity Catalog
y consumidas por Lakeflow, DQX, SQL, AI/BI, Genie y Databricks Apps.

Arquitectura: CSV en un volume de UC → once Bronze y once Silver en Lakeflow → DQX
`validated/quarantine` → cinco Gold y dos Metric Views en SQL Warehouse → Dashboard,
Genie Space y App Streamlit inicial.

Principios: sin información personal; nombres e identificadores ficticios; localidades
y coordenadas públicas aproximadas; visual neutro en azul, verde, ámbar y rojo.

El Dashboard se construye durante la sesión. La App entregada es intencionalmente
simple; modernizar su navegación, diseño e interacciones es el reto posterior.
