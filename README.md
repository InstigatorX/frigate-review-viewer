# frigate-review-viewer
I put together a lightweight webpage that pulls reviews from the Frigate API and displays them inside a Home Assistant iframe. I’m running two Frigate servers — the primary handles all the detection/AI “groovy stuff,” and the secondary just records low-quality streams.

The page grabs review data from the primary server, but when I click an event, it loads the matching recording from the secondary server. Since I travel a lot, trying to stream 4K recordings remotely is brutal, so this setup lets me review events quickly without hammering my bandwidth. Yeah, it adds a bit of extra compute/storage overhead, but I’m totally fine with that trade-off.

Everything is super simple: a single HTML file sitting in /config/www, a small Python script in /config, and a couple of HA automations to tie it all together. I've added color coded severity (camera name changes color), AI summary, filtering, and hover text.

Install

1. Copy the frigate_review.html to the /config/www directory in Home Assistant. Edit this section to reflect your PRIMARY and SECONDARY Frigate servers...
  const NVR = {
    LOCAL:  "PRIMARY_SERVER",
    REMOTE: "SECONDARY_SERVER",
    autoVodHost() {
      // Default for "auto" mode
      return this.REMOTE;
    }
  };
2. Copy build_frigate_day_log.py to the /config directory. You'll need to edit the API IP addresses to suit your environment. 192.168.86.244 is my primary Frigate where the reviews are pull and 192.168.86.243 is my record-only secondary server.
3. Import the automations in to HA. 1st one is the webhook that triggers when current day is selected. That way its always most current. 2nd automation does a final pull at 12:10am for the prior days events. This speeds things up versus pulling each day dynamically.
4. Script is basically a seed for the last 30 days to get things going. Use/modify as needed.

Here's how it works...

build_frigate_day_log.py pulls reviews via Frigate API and converts to a markdown file that is then used by frigate_review.html to display the results. I originally started this as simple GenAI summary viewer in Home Assistant with a markdown card so feel free to use the log files that way. Each day @ 12:10am the prior days reviews are pulled and used to view. The current day is pulled each time the current day is selected.
