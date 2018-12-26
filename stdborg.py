# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from uniborg import Uniborg
import api_key

logging.basicConfig(level=logging.INFO)

borg = Uniborg(
        "stdborg",
        plugin_path="stdplugins",
        connection_retries=None,
        api_id=api_key.id,
        api_hash=api_key.hash
)

borg.run_until_disconnected()
