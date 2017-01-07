server_port = 9876
max_result_check = 1000
show_result_num = 100
max_tags = 5
geo_servers = {
    'msk.foot': ('/home/legin/osrm/Project-OSRM/build/osrm-routed /home/legin/maps/msk_foot/RU-MOW.osrm -p 5001 &',
                 'http://localhost:5001/route/v1/driving/'),
    'msk.car': ('/home/legin/osrm/Project-OSRM/build/osrm-routed /home/legin/maps/msk_car/RU-MOW.osrm -p 5000 &',
                'http://localhost:5000/route/v1/driving/'),
    'kzn.car':('/home/legin/osrm/Project-OSRM/build/osrm-routed /home/legin/maps/kzn_car/RU-TA.osrm -p 5002 &',
                'http://localhost:5002/route/v1/driving/'),
    'kzn.foot':('/home/legin/osrm/Project-OSRM/build/osrm-routed /home/legin/maps/kzn_foot/RU-TA.osrm -p 5003 &',
                'http://localhost:5003/route/v1/driving/')}
w2v_path = '/home/legin/kudablyat_git/w2v_vectors'
w2v_cache=10000
