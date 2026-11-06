"""
@file test_challenger_m1_it3_adversarial_clean_emoji.py
@description Challenger M1 Iteration 3 针对 _clean_emoji 极限脏字符渗透压测套件
覆盖多层组合字符、肤色修饰符、国旗序列、零宽连字/断字符、变体选择符 (VS-1 至 VS-16)、
几何图形、星号符号、键帽序列等极限用例，验证医疗中英数及单位 100% 完好无损，
绝无残缺字节与乱码。全域零 Emoji，函数级中文四要素注释覆盖率 100%。

@param 无 独立自动化测试套件
@returns unittest / pytest 断言结果
@route tests/test_challenger_m1_it3_adversarial_clean_emoji.py
@throws AssertionError 断言不满足时抛出
"""

import os
import sys
import unittest

# 将工程路径加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.coze_service import _clean_emoji


class TestChallengerCleanEmojiAdversarial(unittest.TestCase):
    """针对 Coze _clean_emoji 极限脏字符对抗渗透压测集"""

    def test_01_multilayer_composite_and_skin_tone_modifiers(self):
        """压测 01: 校验多层组合字符、职业修饰及肤色修饰符被彻底剔除且不留残片

        @param 无
        @returns 无
        @route tests/test_challenger_m1_it3_adversarial_clean_emoji.py/test_01
        @throws AssertionError
        """
        # 1. 主治医师组合表情: Man (U+1F468) + ZWJ (U+200D) + Aesculapius (U+2695) + VS-16 (U+FE0F)
        # 2. 浅肤色护士: Person (U+1F9D1) + Light skin (U+1F3FC) + ZWJ (U+200D) + Aesculapius + VS-16
        # 3. 独立中等肤色修饰符: Fitzpatrick Medium (U+1F3FD)
        # 4. 家庭多层组合: Man + ZWJ + Woman + ZWJ + Girl + ZWJ + Boy
        test_input = (
            "科室会诊专家: "
            "\U0001f468\u200d\u2695\ufe0f 张主任 与 "
            "\U0001f9d1\U0001f3fc\u200d\u2695\ufe0f 李护士长, "
            "病区状态: \U0001f44d\U0001f3fd 优良, "
            "家属随访: \U0001f468\u200d\U0001f469\u200d\U0001f467\u200d\U0001f466 配合."
        )

        cleaned = _clean_emoji(test_input)

        # 验证所有 ZWJ、变体符、肤色符全数剥离
        self.assertNotIn("\u200d", cleaned, "ZWJ 零宽连接符必须被彻底剥离")
        self.assertNotIn("\ufe0f", cleaned, "VS-16 变体选择符必须被彻底剥离")
        self.assertNotIn("\U0001f3fc", cleaned, "Fitzpatrick 肤色修饰符必须被剥离")
        self.assertNotIn("\U0001f3fd", cleaned, "Fitzpatrick 肤色修饰符必须被剥离")
        self.assertNotIn("\U0001f468", cleaned, "SMP 平面人物表情必须被剥离")
        self.assertNotIn("\u2695", cleaned, "蛇杖杂项符号必须被剥离")

        # 验证业务文字 100% 完好
        expected_text = "科室会诊专家:  张主任 与  李护士长, 病区状态:  优良, 家属随访:  配合."
        self.assertEqual(cleaned, expected_text, "清洗后文本与预期纯净文本完全匹配")

    def test_02_regional_indicator_and_flag_sequences(self):
        """压测 02: 校验区域指示符组成的国旗序列与细分行政区国旗被彻底过滤

        @param 无
        @returns 无
        @route tests/test_challenger_m1_it3_adversarial_clean_emoji.py/test_02
        @throws AssertionError
        """
        # 国旗序列: CN (U+1F1E8 U+1F1F3), US (U+1F1FA U+1F1F8)
        # 细分行政区旗帜: U+1F3F4 U+E0067 U+E0062 U+E0065 U+E006E U+E0067 U+E007F (England)
        flag_input = (
            "进口高值物资产地: \U0001f1e8\U0001f1f3 中国制造, "
            "对标参照: \U0001f1fa\U0001f1f8 美国FDA, "
            "合作基地: \U0001f3f4\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f 英国."
        )

        cleaned = _clean_emoji(flag_input)

        self.assertNotIn("\U0001f1e8", cleaned)
        self.assertNotIn("\U0001f1f3", cleaned)
        self.assertNotIn("\U0001f1fa", cleaned)
        self.assertNotIn("\U0001f1f8", cleaned)
        self.assertNotIn("\U0001f3f4", cleaned)
        self.assertNotIn("\U000e007f", cleaned)
        self.assertIn("进口高值物资产地:  中国制造", cleaned)
        self.assertIn("对标参照:  美国FDA", cleaned)
        self.assertIn("合作基地:  英国.", cleaned)

    def test_03_variation_selectors_vs1_to_vs16_and_keycaps(self):
        """压测 03: 校验全套变体选择符 (VS-1 至 VS-16) 及封闭键帽字符清洗

        @param 无
        @returns 无
        @route tests/test_challenger_m1_it3_adversarial_clean_emoji.py/test_03
        @throws AssertionError
        """
        # VS-1 至 VS-16 (U+FE00 到 U+FE0F)
        vs_chain = "".join(chr(0xFE00 + i) for i in range(16))
        # 键帽数字: 1 + VS16 + Keycap (U+20E3), # + VS16 + Keycap
        keycap_input = f"优先级别: 1\ufe0f\u20e3 紧急, 批次标签: #\ufe0f\u20e3 重要 {vs_chain} 归档."

        cleaned = _clean_emoji(keycap_input)

        for i in range(16):
            self.assertNotIn(chr(0xFE00 + i), cleaned, f"VS-{i+1} 变体选择符必须被完全移除")
        self.assertNotIn("\u20e3", cleaned, "Combining Enclosing Keycap 必须被完全移除")
        self.assertIn("优先级别: 1 紧急", cleaned)
        self.assertIn("批次标签: # 重要  归档.", cleaned)

    def test_04_geometric_shapes_and_stars_and_dingbats(self):
        """压测 04: 校验几何图形 (U+25A0~U+25FF)、星号 (U+2B50等) 与装饰符号杂项

        @param 无
        @returns 无
        @route tests/test_challenger_m1_it3_adversarial_clean_emoji.py/test_04
        @throws AssertionError
        """
        # U+2B50 (五角星), U+2728 (闪烁), U+25A0 (黑方块), U+25B6 (右三角), U+25CF (黑圆), U+231A (手表), U+23F0 (闹钟)
        symbols_input = (
            "质检评定: \u2b50\u2b50\u2b50\u2b50\u2b50 特级, "
            "状态标识: \u25a0 正常 \u25b6 进行中 \u25cf 完成, "
            "时钟标记: \u231a \u23f0 \u2728 达标."
        )

        cleaned = _clean_emoji(symbols_input)

        self.assertNotIn("\u2b50", cleaned)
        self.assertNotIn("\u2728", cleaned)
        self.assertNotIn("\u25a0", cleaned)
        self.assertNotIn("\u25b6", cleaned)
        self.assertNotIn("\u25cf", cleaned)
        self.assertNotIn("\u231a", cleaned)
        self.assertNotIn("\u23f0", cleaned)
        self.assertIn("质检评定:  特级", cleaned)
        self.assertIn("状态标识:  正常  进行中  完成", cleaned)

    def test_05_medical_specialty_terms_units_and_numbers_preservation(self):
        """压测 05: 校验医疗专有名词、UDI批号、计量单位与微量符号 100% 完好无损

        @param 无
        @returns 无
        @route tests/test_challenger_m1_it3_adversarial_clean_emoji.py/test_05
        @throws AssertionError
        """
        medical_corpus = (
            "产品名称: 冠状动脉球囊扩张导管 (PTCA Balloon Catheter, 2.50mm×15mm), "
            "院内编码: HIGH-2026-X889, UDI-DI: 06971234567890, 批号: LOT-20261105/99A, "
            "存储条件: 2℃~8℃, 湿度≤60%, 气压≥86kPa, 浓度: 0.9% NaCl, 单价: 12800.50元, "
            "有效载荷: 500μg±5μg, 重量: 25.4mg, 容积: 50ml, 规格: 10支/盒."
        )

        cleaned = _clean_emoji(medical_corpus)

        self.assertEqual(cleaned, medical_corpus, "严禁篡改任何合法医疗中英文字符、单位及符号")
        self.assertIn("℃", cleaned, "温度单位 ℃ 不得被误杀")
        self.assertIn("μg", cleaned, "微克单位 μg 不得被误杀")
        self.assertIn("±", cleaned, "公差符号 ± 不得被误杀")
        self.assertIn("≤", cleaned, "不等号 ≤ 不得被误杀")
        self.assertIn("≥", cleaned, "不等号 ≥ 不得被误杀")
        self.assertIn("×", cleaned, "乘号 × 不得被误杀")
        self.assertIn("%", cleaned, "百分号 % 不得被误杀")

    def test_06_byte_integrity_and_anti_corruption_fuzz(self):
        """压测 06: 极限模糊混杂输入下，校验 UTF-8 编码解码无截断、无残缺字节与无乱码

        @param 无
        @returns 无
        @route tests/test_challenger_m1_it3_adversarial_clean_emoji.py/test_06
        @throws AssertionError
        """
        # 构建超密集交错混杂串 (医疗词汇与各类 SMP/BMP/控制符紧挨且无空格)
        dense_dirty = (
            "无菌\U0001f489注射器\u26a0\ufe0f批号\U0001f468\u200d\u2695\ufe0f"
            "LOT2026A\u2b50\u2b50\u231a50ml\U0001f3e5合格\ufe0f\u20e3"
        )

        cleaned = _clean_emoji(dense_dirty)

        # 1. 验证可正常执行 UTF-8 编码解码
        raw_bytes = cleaned.encode("utf-8")
        decoded_back = raw_bytes.decode("utf-8")
        self.assertEqual(cleaned, decoded_back, "清洗输出必须具备完全有效的 UTF-8 字节结构")

        # 2. 验证绝无 Unicode 替换字符 (U+FFFD)
        self.assertNotIn("\ufffd", cleaned, "不得遗留 Unicode 乱码替换字符 U+FFFD")

        # 3. 验证紧邻的中英文字符严丝合缝拼接，无截断丢失
        expected = "无菌注射器批号LOT2026A50ml合格"
        self.assertEqual(cleaned, expected, "紧邻医疗词汇在 Emoji 剔除后无损精准缝合")

    def test_07_empty_null_and_whitespace_boundaries(self):
        """压测 07: 边界值校验 (None、空串、纯空白、纯 Emoji 串)

        @param 无
        @returns 无
        @route tests/test_challenger_m1_it3_adversarial_clean_emoji.py/test_07
        @throws AssertionError
        """
        self.assertEqual(_clean_emoji(""), "")
        self.assertEqual(_clean_emoji(None), "")
        self.assertEqual(_clean_emoji("   \t\n  "), "   \t\n  ")
        # 纯 Emoji 串清洗后应退化为空字符串
        pure_emojis = "\U0001f489\U0001f48a\U0001f3e5\u2728\u2b50\ufe0f\u200d"
        self.assertEqual(_clean_emoji(pure_emojis), "")


if __name__ == "__main__":
    unittest.main()
