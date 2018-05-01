import time
import random
import datetime
import telepot
import subprocess
import requests
import digitalocean

"""
After **inserting token** in the source code, run it:

```
$ python2.7 diceyclock.py
```

[Here is a tutorial](http://www.instructables.com/id/Set-up-Telegram-Bot-on-Raspberry-Pi/)
teaching you how to setup a bot on Raspberry Pi. This simple bot does nothing
but accepts two commands:

- `/roll` - reply with a random integer between 1 and 6, like rolling a dice.
- `/time` - reply with the current time, like a clock.
"""
def change_record_data(api_token, domain_str, record_id, new_data):
	domain_obj = None
	while domain_obj is None:
		try:
			manager = digitalocean.Manager(token=api_token)
			domain_obj = manager.get_domain(domain_str)
		except:
			pass

	record = None
	while record is None:
		try:
			record = digitalocean.Record.get_object(api_token, domain_obj, record_id)
		except:
			pass

	while (record.data != new_data):
		#print (record.data)
		record.data = new_data
		try:
			record.save()
			record.load()
		except:
			pass

def do_api_object_search(source, name):

	for obj in source:
		if obj.name == name:
			return obj

	return False

def do_api_object_search_manager(manager, obj, name):

	if obj == "Droplet":
		my_obj = manager.get_all_droplets()

	elif obj == "Snapshot":
		my_obj = manager.get_all_snapshots()

	return do_api_object_search(my_obj,name)



def wait_while_not_found(manager,obj, name):

	my_obj = False
	if obj == "Droplet":
		my_obj = manager.get_all_droplets()

	elif obj == "Snapshot":
		my_obj = manager.get_all_snapshots()

	while isinstance(do_api_object_search(my_obj, name), bool):
		if obj == "Droplet":
			my_obj = manager.get_all_droplets()

		elif obj == "Snapshot":
			my_obj = manager.get_all_snapshots()
		print ("Not Found")

	time.sleep(2)

	if obj == "Droplet":
		while do_api_object_search(my_obj, name).ip_address is None:
			my_obj = manager.get_all_droplets()
			print ("Machine Not Ready")

	elif obj == "Snapshot":
		pass

	time.sleep(3)
	print ("Found and Ready")
	return my_obj

def start_server(chat_id, manager, do_token):

	if isinstance(do_api_object_search_manager(manager, "Droplet", "MCServer"), bool):
		bot.sendMessage(chat_id, "Looking for MCServer Snapshot...")

		while isinstance(do_api_object_search_manager(manager, "Snapshot", "MCServer"), bool):
			time.sleep(1)

		bot.sendMessage(chat_id, "MCServer Snapshot Found!")
		time.sleep(1)
		bot.sendMessage(chat_id, "Fetching MCServer Snapshot...")
		time.sleep(5)

		my_snap = do_api_object_search_manager(manager, "Snapshot", "MCServer")

		bot.sendMessage(chat_id, "Configuring SSH Access...")
		time.sleep(5)
		my_ssh = manager.get_all_sshkeys()

		bot.sendMessage(chat_id, "Creating Droplet...")
		droplet = digitalocean.Droplet(token=do_token,
									   name='MCServer',
									   region='sgp1', # Singapore 1
									   image=my_snap.id, # Ubuntu 14.04 x64
									   size_slug='s-1vcpu-2gb',
									   ssh_keys=my_ssh)  # 1024MB
		droplet.create()
		time.sleep(5)

		bot.sendMessage(chat_id, "Waiting for Server to be ready...")
		while isinstance(do_api_object_search_manager(manager, "Droplet", "MCServer"), bool):
			time.sleep(1)

		time.sleep(1)

		while do_api_object_search_manager(manager, "Droplet", "MCServer").ip_address is None:
			time.sleep(1)

		time.sleep(3)

		mc_droplet = do_api_object_search_manager(manager,"Droplet","MCServer")
		if isinstance(mc_droplet, bool):
			bot.sendMessage(chat_id, 'Something bad just happened. Chotto matte kudasai.')
		else:
			domain_name = " "
			first_record = 0
			second_record = 0
			change_record_data(do_token, domain_name, first_record, mc_droplet.ip_address)
			change_record_data(do_token, domain_name, second_record, mc_droplet.ip_address)
			bot.sendMessage(chat_id, 'MCServer Address : ' + mc_droplet.ip_address)
			bot.sendMessage(chat_id, 'or minecraft.' + domain_name)

		bot.sendMessage(chat_id, 'Destroying Snapshot...')
		my_snap.destroy()

		while not isinstance(do_api_object_search_manager(manager, "Snapshot", "MCServer"), bool):
			time.sleep(1)

		bot.sendMessage(chat_id, 'Snapshot Destroyed')
	else:
		bot.sendMessage(chat_id, 'Server already running!')

def destroy_server(chat_id, manager):
	if not isinstance(do_api_object_search_manager(manager, "Droplet", "MCServer"), bool):

		bot.sendMessage(chat_id, 'Fetching Droplet...')
		while isinstance(do_api_object_search_manager(manager, "Droplet", "MCServer"), bool):
			time.sleep(1)

		mc_droplet = do_api_object_search_manager(manager,"Droplet","MCServer")

		bot.sendMessage(chat_id, 'Shutting down Droplet...')
		mc_droplet.shutdown()
		time.sleep(10)

		while do_api_object_search_manager(manager, "Droplet", "MCServer").status == "active" :
			time.sleep(5)
			mc_droplet.shutdown()

		bot.sendMessage(chat_id, 'Server Shutdown!')
		time.sleep(3)
		bot.sendMessage(chat_id, 'Creating Snapshot...')
		mc_droplet.take_snapshot('MCServer')
		time.sleep(5)
		while isinstance(do_api_object_search_manager(manager, "Snapshot", "MCServer"), bool):
			time.sleep(1)
		time.sleep(5)
		bot.sendMessage(chat_id, 'Snapshot Created...')

		bot.sendMessage(chat_id, 'Destroying Droplet...')
		mc_droplet.destroy()
		time.sleep(10)
		while not isinstance(do_api_object_search_manager(manager, "Droplet", "MCServer"), bool):
			time.sleep(1)
		bot.sendMessage(chat_id, 'Droplet Destroyed!')

	else :
		bot.sendMessage(chat_id, 'Server is not running yet!')

def handle(msg):
    chat_id = msg['chat']['id']
    command = msg['text']
    api_token = " "
    manager = digitalocean.Manager(token=api_token)

    print ("Got command: "+ command)

    if command == '/start_server':
        start_server(chat_id, manager, api_token)
    elif command == '/destroy_server':
        destroy_server(chat_id, manager)
    elif command == '/time':
        bot.sendMessage(chat_id, str(datetime.datetime.now()))
    elif command == '/server_ip':
        if not isinstance(do_api_object_search_manager(manager, "Droplet", "MCServer"), bool):
            bot.sendMessage(chat_id, "MCServer Address : " + do_api_object_search_manager(manager, "Droplet", "MCServer").ip_address)
        else:
            bot.sendMessage(chat_id, "Server is not running yet")

bot = telepot.Bot(' ')
bot.message_loop(handle)
print ('I am listening ...')

while 1:
    time.sleep(10)
