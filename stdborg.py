import logging

from uniborg import Uniborg

logging.basicConfig(level=logging.INFO)

borg = Uniborg("stdborg", plugin_path="stdplugins")

borg.run()
