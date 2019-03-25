from zabbix.api import ZabbixAPI
import json

def triggers_actions(triggers_id, actions_id, zapi):
    triggers_actions = dict()
    actions = zapi.action.get(selectFilter="extend" ,output=["filter"], actionids = actions_id)
    for triggerid in triggers_id:
        trigger_info = zapi.trigger.get(triggerids = triggerid, 
                                        expandDescription=True, 
                                        selectGroups="groupid", 
                                        selectHosts="hostid", 
                                        selectTags="extend",
                                        selectItems="itemid", 
                                        output=["triggerid", "description", "priority", "templateid"])
        #print(json.dumps(trigger_info[0], indent=4))

        trigger_data = dict()
        items = [ item["itemid"] for item in trigger_info[0]["items"]]
        applications = zapi.application.get(itemids=items, output = ["name"])

        app_name = [app["name"] for app in applications]
        groups = [gr["groupid"] for gr in trigger_info[0]["groups"]]
        hosts = [h["hostid"] for h in trigger_info[0]["hosts"]]
        tags = list({t["tag"] for t in trigger_info[0]["tags"]})
        tags_values = trigger_info[0]["tags"]

        trigger_data["0"] = groups
        trigger_data["1"] = hosts
        trigger_data["2"] = [trigger_info[0]["triggerid"]]
        trigger_data["3"] = [trigger_info[0]["description"]]
        trigger_data["4"] = [trigger_info[0]["priority"]]
        trigger_data["13"] = [trigger_info[0]["templateid"]]
        trigger_data["15"] = app_name
        trigger_data["25"] = tags
        trigger_data["26"] = tags_values


        def var_resolver(var):
            """ cond_type
                0 - группа узлов сети;
                1 - узел сети;
                2 - триггер;
                3 - имя триггера;
                4 - важность триггера;
                6 - период времени; 
                13 - шаблон узла сети;
                15 - группа элементов данных;
                16 - проблема подавлена; 
                25 - тег события;
                26 - значения тега события."""
            """operators
                0 - (по умолчанию) =;
                1 - <>;
                2 - содержит;
                3 - не содержит;
                4 - в;
                5 - >=;
                6 - <=;
                7 - не в;
                8 - соответствует;
                9 - не соответствует;
                10 - Да;
                11 - Нет. """
            operators_simple = {
                "0": " in ",
                "1": " not in ",
                "4": " in ",
                "7": " not in "
            }
            if var["conditiontype"] in ["6", "16"]:
                res = True
            else:
                if var["operator"] in operators_simple:
                    if var["conditiontype"] != "26":
                        res = eval('var["value"] %s trigger_data[var["conditiontype"]]' % operators_simple[var["operator"]])
                    elif var["conditiontype"] == "26":
                        res = eval('{"tag" : var["value2"], "value" : var["value"]} %s trigger_data[var["conditiontype"]]' % operators_simple[var["operator"]])

                elif var["operator"] == "2":
                    res = False 
                    for app in trigger_data[var["conditiontype"]]:
                        if var["value"] in app:
                            res = True

                elif var["operator"] == "3":
                    res = False
                    for app in trigger_data[var["conditiontype"]]:
                        if var["value"] not in app:
                            res = True

                elif var["operator"] == "5":
                    res = False 
                    for app in trigger_data[var["conditiontype"]]:
                        if int(var["value"]) >=  int(app):
                            res = True
                elif var["operator"] == "6":
                    res = False 
                    for app in trigger_data[var["conditiontype"]]:
                        if int(var["value"]) <=  int(app):
                            res = True
            return res



        actions_id = []
        for action in actions:
            if action["filter"]["eval_formula"]:
                for cond in action["filter"]["conditions"]:
                    #print(cond)
                    #резолвер кондишенов в переменные формулы. приримает cond возвращает res
                    res = var_resolver(cond)
                    exec("%s = %s" % (cond["formulaid"], res))
                    #print(cond, res)
                    
                action_complite = eval(action["filter"]["eval_formula"])
                if action_complite:
                    actions_id.append(action["actionid"])
        triggers_actions[triggerid] = actions_id
    return triggers_actions

def main():
    ZBX_USER = ""
    ZBX_PASS = ""
    ZBX_URL = ""
    zapi = ZabbixAPI(ZBX_URL, user = ZBX_USER, password = ZBX_PASS)

    triggerid = []
    actions = zapi.action.get(filter={"eventsource":"0", "status": "0"})
    print(triggers_actions(triggerid,actions,zapi))

if __name__ == '__main__':
    main()