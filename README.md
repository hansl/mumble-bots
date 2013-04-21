# mumble-bots

A list of bots for Mumble Servers. Also, a framework for easily build your own bots in Python.


# Commanding bots
The API is simple; use slash commands in messages to bots.

List of supported commands by default:
1. /add
2. 


# Included Bots

## AFKMove
A bot

## Echo
A test bot that reply back a message to the sender. This does not support any bang or slash commands.

## Eve
A bot that eavesdrop on a channel and replays it to another channel, potentially with a delay.

## Dice


# Using a Bot

## Example Usage
    
    #!/bin/python
    #
    # Simple bot that will move all users on the server to a channel
    # when issued the command /moveall.
    # Set the channel ID with /set channel_id 1
    # Or the channel name with /set channel_name "the name"
    # You can manage the rights of this bot by sending it the
    # /add_right message, e.g. /add_right UserName moveall
    # or /remove_right.
    import mumble

    class UserMoveBot(mumble.AdvanceBot):
      def __init__(self, server, name = "EchoBot by HansL"):
        mumble.CommandBot.__init__(self, server, name = name)
        self.args = {
	      'max_idle': 60
        }
    
      def stopping(self):
        self.thread.keep_going = False

	  def on_

      def on_command_moveall(self, *):
        for user in self.users():
          user.move_to(self.get_channel_by_id(self.vars["channel_id"]))

	if __name__ == '__main__':
	  # Start the bot
	  bot = UserMoveBot(mumble.Server("example.com"))
	  bot.join()
