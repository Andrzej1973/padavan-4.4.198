"""Read literal source-preparation recipe without running source mutations."""
import ast
from pathlib import Path


def expected_steps(path=None):
    path = Path(path) if path else Path(__file__).with_name('prepare-source-integration.py')
    tree = ast.parse(path.read_text())
    names = ('PERSISTENCE_CHECKS', 'PERSISTENCE_ADAPTER_CHECKS', 'SOURCE_PREPARERS')
    values = {}
    for name in names:
        declarations = [node for node in tree.body if isinstance(node, ast.Assign)
                        and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
        if len(declarations) != 1:
            raise ValueError('Missing/duplicate literal recipe: '+name)
        sequence = ast.literal_eval(declarations[0].value)
        if not isinstance(sequence, tuple) or not sequence or any(not isinstance(item, str) or not item for item in sequence):
            raise ValueError('Invalid source preparation recipe: '+name)
        values[name] = sequence
    steps = ['../iot/'+item for item in values[names[0]]+values[names[1]]]
    steps += list(values[names[2]])
    steps += ['prepare-abi-probe.py', 'read-abi-probe.py', 'prepare-package-integration.py']
    if len(steps) != len(set(steps)):
        raise ValueError('Duplicate source preparation step')
    return steps
