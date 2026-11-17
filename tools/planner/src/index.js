/* Planner: starts the workflow "Dagelijkse verversing" on GitHub at the Dutch times of its schedule.

   GitHub's own schedule can start a run late or not at all. This Worker is called by a Cloudflare
   cron trigger every five minutes (in UTC), looks whether that moment is a slot of the schedule in
   Dutch time, and if so asks GitHub to start the workflow (workflow_dispatch). It starts nothing
   while a run is running or waiting, or when one has just succeeded.

   Needs the secret GITHUB_TOKEN and the variables GITHUB_REPO, WORKFLOW and REF (wrangler.jsonc). */

import { slotOp, start, meld } from "./planner.js";

// Only the handler is exported here: Cloudflare refuses a Worker whose main module exports anything else.
export default {
  async scheduled(controller, env, ctx) {
    const slot = slotOp(controller.scheduledTime);
    if (!slot) return;
    try {
      await start(slot, controller.scheduledTime, env);
    } catch (fout) {
      meld("fout", slot, fout.message);
      throw fout;   // so that Cloudflare shows the invocation as failed
    }
  },
};
