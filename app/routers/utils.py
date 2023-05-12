from datetime import datetime

def model_to_dict(model_instance):
    return {column.name: getattr(model_instance, column.name) for column in model_instance.__table__.columns}

def parse_interval_time(interval):
        start_time_str, end_time_str = interval.split('-')
        start_time = datetime.strptime(start_time_str, '%H:%M')
        end_time = datetime.strptime(end_time_str, '%H:%M')
        return start_time, end_time