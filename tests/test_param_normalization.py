from api.services.matrix_service import matrix_service


def test_all_standard_names_map_to_themselves():
    for pid, name in matrix_service.parameters.items():
        assert matrix_service.get_param_id(name) == pid


def test_alias_energy_consumption():
    assert matrix_service.get_param_id("能量消耗") == "19"
    assert matrix_service.get_param_id("续航") == "19"
    assert matrix_service.get_param_id("电池续航") == "19"


def test_numeric_prefix_prefers_name_over_number():
    # 模型写的是 26，但名称是测量精度，应映射到 28
    assert matrix_service.get_param_id("26. 测量精度") == "28"
    assert matrix_service.get_param_id("20 油耗") == "19"
    assert matrix_service.get_param_id("19") == "19"


def test_verb_and_state_cleanup():
    assert matrix_service.get_param_id("提高速度") == "9"
    assert matrix_service.get_param_id("增加楼层高度") == "3"
    assert matrix_service.get_param_id("电梯等待时间变长") == "25"


def test_containment_alias_prefers_longest_match():
    assert matrix_service.get_param_id("控制系统复杂性") == "37"
    assert matrix_service.get_param_id("刚度不足") == "14"
    assert matrix_service.get_param_id("内部容积") == "7"


def test_fuzzy_match():
    assert matrix_service.get_param_id("运动物体重量") == "1"


def test_unknown_parameter_returns_none():
    assert matrix_service.get_param_id("外星参数") is None
    assert matrix_service.get_param_id("") is None
