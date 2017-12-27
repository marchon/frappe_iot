# -*- coding: utf-8 -*-
# Copyright (c) 2017, Dirk Chang and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import redis
import uuid
from frappe import throw, msgprint, _
from iot.doctype.iot_device.iot_device import IOTDevice
from iot.doctype.iot_hdb_settings.iot_hdb_settings import IOTHDBSettings


def valid_auth_code(auth_code=None):
	auth_code = auth_code or frappe.get_request_header("HDB-AuthorizationCode")
	if not auth_code:
		throw(_("HDB-AuthorizationCode is required in HTTP Header!"))
	frappe.logger(__name__).debug(_("HDB-AuthorizationCode as {0}").format(auth_code))

	user = IOTHDBSettings.get_on_behalf(auth_code)
	if not user:
		throw(_("Authorization Code is incorrect!"))
	# form dict keeping
	form_dict = frappe.local.form_dict
	frappe.set_user(user)
	frappe.local.form_dict = form_dict


def get_post_json_data():
	if frappe.request.method != "POST":
		throw(_("Request Method Must be POST!"))
	ctype = frappe.get_request_header("Content-Type")
	if "json" not in ctype.lower():
		throw(_("Incorrect HTTP Content-Type found {0}").format(ctype))
	data = frappe.request.get_data()
	if not data:
		throw(_("JSON Data not found!"))
	return json.loads(data)


@frappe.whitelist(allow_guest=True)
def get_action_result(id):
	if frappe.session.user == "Guest":
		valid_auth_code()
	client = redis.Redis.from_url(IOTHDBSettings.get_redis_server() + "/7")
	str = client.get(id)
	if str:
		return json.loads(str)


@frappe.whitelist(allow_guest=True)
def send_action(channel, action=None, id=None, device=None, data=None):
	if frappe.session.user == "Guest":
		valid_auth_code()
	data = data or get_post_json_data()
	id = id or str(uuid.uuid1()).upper()

	if not device:
		throw(_("Device SN does not exits!"))

	doc = frappe.get_doc("IOT Device", device)
	if not doc.has_permission("write"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	client = redis.Redis.from_url(IOTHDBSettings.get_redis_server())
	args = {
		"id": id,
		"device": device,
		"data": data,
	}
	if action:
		args.update({
			"action": action,
		})
	r = client.publish("device_" + channel, json.dumps(args))
	if r <= 0:
		throw(_("Redis message published, but no listener!"))
	return id


@frappe.whitelist(allow_guest=True)
def app_list():
	data = get_post_json_data()
	return send_action("app", action="list", id=data.get("id"), device=data.get("device"), data="1")


@frappe.whitelist(allow_guest=True)
def app_install():
	data = get_post_json_data()
	return send_action("app", action="install", id=data.get("id"), device=data.get("device"), data=data.get("data"))


@frappe.whitelist(allow_guest=True)
def app_uninstall():
	data = get_post_json_data()
	return send_action("app", action="uninstall", id=data.get("id"), device=data.get("device"), data=data.get("data"))


@frappe.whitelist(allow_guest=True)
def app_upgrade():
	data = get_post_json_data()
	return send_action("app", action="upgrade", id=data.get("id"), device=data.get("device"), data=data.get("data"))


@frappe.whitelist(allow_guest=True)
def app_conf():
	data = get_post_json_data()
	return send_action("app", action="conf", id=data.get("id"), device=data.get("device"), data=data.get("data"))


@frappe.whitelist(allow_guest=True)
def app_start():
	'''
	Start application, data example: {"inst": "bms", "conf": "{}"} conf is optional
	:return:
	'''
	data = get_post_json_data()
	return send_action("app", action="start", id=data.get("id"), device=data.get("device"), data=data.get("data"))


@frappe.whitelist(allow_guest=True)
def app_stop():
	'''
	Stop application, data example: {"inst": "bms", "reason": "debug stop"}
	:return:
	'''
	data = get_post_json_data()
	return send_action("app", action="stop", id=data.get("id"), device=data.get("device"), data=data.get("data"))


@frappe.whitelist(allow_guest=True)
def sys_upgrade():
	if frappe.session.user == "Guest":
		valid_auth_code()
	data = get_post_json_data()
	return send_action("sys", action="upgrade", id=data.get("id"), device=data.get("device"), data=data.get("data"))


@frappe.whitelist(allow_guest=True)
def sys_upgrade_ack():
	data = get_post_json_data()
	return send_action("sys", action="upgrade/ack", id=data.get("id"), device=data.get("device"), data=data.get("data"))


@frappe.whitelist(allow_guest=True)
def sys_enable_data():
	data = get_post_json_data()
	return send_action("sys", action="enable/data", id=data.get("id"), device=data.get("device"), data=data.get("data"))


@frappe.whitelist(allow_guest=True)
def sys_enable_log():
	data = get_post_json_data()
	return send_action("sys", action="enable/log", id=data.get("id"), device=data.get("device"), data=data.get("data"))


@frappe.whitelist(allow_guest=True)
def sys_enable_comm():
	data = get_post_json_data()
	return send_action("sys", action="enable/comm", id=data.get("id"), device=data.get("device"), data=data.get("data"))


@frappe.whitelist(allow_guest=True)
def sys_enable_stat():
	data = get_post_json_data()
	return send_action("sys", action="enable/stat", id=data.get("id"), device=data.get("device"), data=data.get("data"))


@frappe.whitelist(allow_guest=True)
def sys_enable_beta():
	data = get_post_json_data()
	return send_action("sys", action="enable/beta", id=data.get("id"), device=data.get("device"), data=data.get("data"))


@frappe.whitelist(allow_guest=True)
def send_output():
	data = get_post_json_data()
	return send_action("output", id=data.get("id"), device=data.get("device"), data=data.get("data"))


@frappe.whitelist(allow_guest=True)
def send_command():
	data = get_post_json_data()
	return send_action("command", id=data.get("id"), device=data.get("device"), data=data.get("data"))