from sqlalchemy import MetaData, Table, Column, Integer, Strin, ForeignKey, ARRAY

metadata = MetaData()

courier = Table(
    Column("courier_id", Integer, primary_key=True),
    Column("courier_type", String, nullable=False),
    Column("regions", ARRAY(Integer), nullable=False),
    Column("working_hours", String, nullable=False)
)

