# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging

import locust
from locust import LoadTestShape, events

logger = logging.getLogger(__name__)


@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument(
        "--arrival_rate",
        type=float,
        default=1.0,
    )


class ConstantRPSLoadShape(LoadTestShape):
    use_common_options = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.arrival_rate = locust.argument_parser.parse_options().arrival_rate
        self.last_tick = 0

    def tick(self):
        if self.last_tick == 0:
            logger.info("Constant load shape arrival rate: {arrival_rate}".format(arrival_rate=self.arrival_rate))

        run_time = self.get_run_time()
        if run_time < self.runner.environment.parsed_options.run_time:
            self.last_tick = run_time

            new_users = int(self.arrival_rate)
            current_users = self.get_current_user_count()
            user_count = current_users + new_users
            logger.debug(
                "Current users: {current_users}, New users: {new_users}, Target users: {target_users}".format(
                    current_users=current_users, new_users=new_users, target_users=user_count
                )
            )
            # Avoid illegal spawn_rate value of 0
            spawn_rate = max(0.01, new_users)
            return (user_count, spawn_rate)

        self.runner.environment.stop_timeout = 0
        return None
