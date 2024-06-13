from atomic_operator import AtomicOperator

operator = AtomicOperator()


# this will run tests on your local system
print(operator.run(techniques=['T1040'],  atomics_path="/home/vipulp/red-team/redcanaryco-atomic-red-team-ebbf68e/"))