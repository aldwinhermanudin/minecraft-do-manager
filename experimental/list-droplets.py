import digitalocean
import time


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
	
def start_server(manager):

	wait_while_not_found(manager, "Snapshot", "MCServer")

	my_snap = do_api_object_search_manager(manager, "Snapshot", "MCServer")
	
	my_ssh = manager.get_all_sshkeys()
	
	droplet = digitalocean.Droplet(token=api_token,
								   name='MCServer',
								   region='sgp1', # Singapore 1
								   image=my_snap.id, # Ubuntu 14.04 x64
								   size_slug='2gb',
								   ssh_keys=my_ssh)  # 1024MB 
	droplet.create()

	print(wait_while_not_found(manager, "Droplet", "MCServer"))

	time.sleep(3)

	#while not isinstance(do_api_object_search(my_droplets,"MCServer"), bool):

	mc_droplet = do_api_object_search_manager(manager,"Droplet","MCServer")
	if isinstance(mc_droplet, bool):
		return ("MCServer not found")
	else:
		return (mc_droplet.ip_address)
		
	my_snap.destroy()
	
def destroy_server(manager):

	mc_droplet = do_api_object_search_manager(manager,"Droplet","MCServer")
	mc_droplet.shutdown()

	time.sleep(3)
	while do_api_object_search_manager(manager, "Droplet", "MCServer").status == "active" :
		print ("Still Active")
		
	mc_droplet.take_snapshot('MCServer')
	print(wait_while_not_found(manager, "Snapshot", "MCServer"))
	time.sleep(3)
	mc_droplet.destroy()
	time.sleep(3)

api_token = " "

manager = digitalocean.Manager(token=api_token)

print (manager.get_all_sshkeys())
destroy_server(manager)
print ("Server Destroyed")
