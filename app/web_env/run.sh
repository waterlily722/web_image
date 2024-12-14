#!/bin/bash

for i in {1..10}
do
	username="doctor$i"
	password="annotation$i"
	python3 user_data.py "$username" "$password"
done
