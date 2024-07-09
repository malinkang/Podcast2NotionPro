import pendulum

t = pendulum.now(tz="Asia/Shanghai").int_timestamp
print(pendulum.from_timestamp(t, tz="Asia/Shanghai").to_datetime_string())
