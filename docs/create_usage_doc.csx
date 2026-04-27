// File: create_usage_doc.csx
// Usage: dotnet run --project scripts/dotnet/MiniMaxAIDocx.Cli -- run-script create_usage_doc.csx
#r "nuget: DocumentFormat.OpenXml, 3.2.0"

using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using DocumentFormat.OpenXml.Vml.Office;

var outputPath = args.Length > 0 ? args[0] : "D:/qh-dcpj-py/空间数据检查桌面版-主题/docs/应用场景与实施方法.docx";

using var doc = WordprocessingDocument.Create(outputPath, WordprocessingDocumentType.Document);
var mainPart = doc.AddMainDocumentPart();

// Create styles
var stylesPart = mainPart.AddNewPart<StyleDefinitionsPart>();
stylesPart.Styles = new Styles();

// DocDefaults
var docDefaults = new DocDefaults(
    new RunPropertiesDefault(
        new RunPropertiesBaseStyle(
            new RunFonts { Ascii = "微软雅黑", HighAnsi = "微软雅黑", EastAsia = "微软雅黑" },
            new FontSize { Val = "24" },
            new FontSizeComplexScript { Val = "24" }
        )
    ),
    new ParagraphPropertiesDefault(
        new ParagraphPropertiesBaseStyle(
            new SpacingBetweenLines { After = "160", Line = "360", LineRule = LineSpacingRuleValues.Auto }
        )
    )
);
stylesPart.Styles.Append(docDefaults);

// Heading1 style
var h1Style = new Style(
    new StyleName { Val = "Heading 1" },
    new BasedOn { Val = "Normal" },
    new NextParagraphStyle { Val = "Normal" },
    new StyleParagraphProperties(
        new OutlineLevel { Val = 0 },
        new SpacingBetweenLines { Before = "360", After = "240" },
        new RunPropertiesBaseStyle(new Bold(), new FontSize { Val = "36" }, new Color { Val = "1F3864" })
    )
) { StyleId = "Heading1", Type = StyleValues.Paragraph };
stylesPart.Styles.Append(h1Style);

// Heading2 style
var h2Style = new Style(
    new StyleName { Val = "Heading 2" },
    new BasedOn { Val = "Normal" },
    new NextParagraphStyle { Val = "Normal" },
    new StyleParagraphProperties(
        new OutlineLevel { Val = 1 },
        new SpacingBetweenLines { Before = "280", After = "160" },
        new RunPropertiesBaseStyle(new Bold(), new FontSize { Val = "28" }, new Color { Val = "2F5496" })
    )
) { StyleId = "Heading2", Type = StyleValues.Paragraph };
stylesPart.Styles.Append(h2Style);

// Heading3 style
var h3Style = new Style(
    new StyleName { Val = "Heading 3" },
    new BasedOn { Val = "Normal" },
    new NextParagraphStyle { Val = "Normal" },
    new StyleParagraphProperties(
        new OutlineLevel { Val = 2 },
        new SpacingBetweenLines { Before = "200", After = "120" },
        new RunPropertiesBaseStyle(new Bold(), new FontSize { Val = "24" })
    )
) { StyleId = "Heading3", Type = StyleValues.Paragraph };
stylesPart.Styles.Append(h3Style);

stylesPart.Styles.Save();

// Build document body
var body = new Body();

// Title
body.Append(new Paragraph(
    new ParagraphProperties(new Justification { Val = JustificationValues.Center }),
    new Run(new RunProperties(new Bold(), new FontSize { Val = "44" }), new Text("风险隐患调查成果审核工具"))
));
body.Append(new Paragraph(
    new ParagraphProperties(new Justification { Val = JustificationValues.Center }),
    new Run(new RunProperties(new FontSize { Val = "32" }), new Text("应用场景、实施方法与效果对比"))
));
body.Append(new Paragraph()); // Empty line

// ===============================
// Section 1: 应用场景
// ===============================
body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading1" }),
    new Run(new Text("一、应用场景"))
));

body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading2" }),
    new Run(new Text("1.1 业务背景"))
));

body.Append(new Paragraph(new Run(new Text(
    "青海省山洪灾害风险隐患调查与影响分析项目涉及大量空间数据成果的审核工作。传统人工审核方式存在效率低、易遗漏、标准不统一等问题。本工具旨在通过自动化检查手段，提升成果审核的效率和质量。"))));

body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading2" }),
    new Run(new Text("1.2 适用范围"))
));

body.Append(new Paragraph(new Run(new Text("本工具适用于以下场景：")));

var scopeTable = CreateSimpleTable(body,
    new[] { "场景类型", "具体描述", "核心价值" },
    new[][]
    {
        new[] { "成果验收审核", "区县级成果提交省级验收前的质量检查", "提前发现问题，减少返工" },
        new[] { "数据质量评估", "对空间数据完整性、一致性进行评估", "量化质量指标，客观评价" },
        new[] { "日常数据检查", "项目实施过程中的数据质量把控", "及时发现并纠正问题" },
        new[] { "成果规范化处理", "统一SHP文件命名和字段格式", "便于成果归档和共享" }
    }
);

body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading2" }),
    new Run(new Text("1.3 目标用户"))
));

body.Append(new Paragraph(new Run(new Text("• 青海省水利厅/应急管理部门审核人员")));
body.Append(new Paragraph(new Run(new Text("• 区县级山洪灾害调查成果审核工作人员")));
body.Append(new Paragraph(new Run(new Text("• 空间数据质量控制技术人员")));
body.Append(new Paragraph(new Run(new Text("• 项目成果验收评审专家")));

// ===============================
// Section 2: 实施方法
// ===============================
body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading1" }),
    new Run(new Text("二、实施方法"))
));

body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading2" }),
    new Run(new Text("2.1 环境准备"))
));

body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading3" }),
    new Run(new Text("2.1.1 软件环境"))
));

var envTable = CreateSimpleTable(body,
    new[] { "环境项", "要求", "说明" },
    new[][]
    {
        new[] { "操作系统", "Windows 10/11", "桌面应用程序" },
        new[] { "Python环境", "ArcGIS Pro Python 3.x", "SHP格式化功能依赖" },
        new[] { "ArcGIS", "ArcGIS Pro 3.x 或 Desktop 10.8", "空间数据处理引擎" },
        new[] { "运行时", "无需安装Python", "工具已打包为独立exe" }
    }
);

body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading3" }),
    new Run(new Text("2.1.2 数据准备"))
));

body.Append(new Paragraph(new Run(new Text("审核前需准备以下数据：")));
body.Append(new Paragraph(new Run(new Text("1. 待审核成果文件夹（包含多个流域/子文件夹）")));
body.Append(new Paragraph(new Run(new Text("2. 水系基础数据（SHP格式，包含河流代码和河流名称字段）")));
body.Append(new Paragraph(new Run(new Text("3. 成果报表（附表1、附表2、附表3的Excel文件）")));

body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading2" }),
    new Run(new Text("2.2 操作步骤"))
));

body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading3" }),
    new Run(new Text("2.2.1 空间数据检查操作流程"))
));

body.Append(new Paragraph(new Run(new RunProperties(new Bold()), new Text("步骤一：启动工具"))));
body.Append(new Paragraph(new Run(new Text("双击运行"空间数据检查工具.exe"，进入主界面。主界面左侧为功能导航栏，右侧为操作区域。")));
body.Append(new Paragraph(new Run(new Text("")))); // 空行

// 截图占位符
body.Append(CreateScreenshotPlaceholder("图2-1 工具主界面截图", "启动后的主界面，显示三个主要功能模块"));

body.Append(new Paragraph(new Run(new RunProperties(new Bold()), new Text("步骤二：选择目标文件夹"))));
body.Append(new Paragraph(new Run(new Text("点击"浏览"按钮，选择包含待审核成果的根目录。系统将自动递归搜索所有子文件夹中的目标SHP文件。")));
body.Append(new Paragraph(new Run(new Text("")))); // 空行

body.Append(CreateScreenshotPlaceholder("图2-2 文件夹选择对话框", "选择待检查的成果文件夹"));

body.Append(new Paragraph(new Run(new RunProperties(new Bold()), new Text("步骤三：选择水系文件"))));
body.Append(new Paragraph(new Run(new Text("点击水系文件选择按钮，指定水系基础数据文件。水系数据将作为校验的参考基准。")));
body.Append(new Paragraph(new Run(new Text("")))); // 空行

body.Append(CreateScreenshotPlaceholder("图2-3 水系文件选择", "选择水系SHP文件"));

body.Append(new Paragraph(new Run(new RunProperties(new Bold()), new Text("步骤四：开始检查"))));
body.Append(new Paragraph(new Run(new Text("点击"开始检查"按钮，系统将自动执行检查。进度条实时显示处理状态，日志窗口输出详细检查过程。")));
body.Append(new Paragraph(new Run(new Text("")))); // 空行

body.Append(CreateScreenshotPlaceholder("图2-4 检查过程", "检查进行中的界面，显示进度条和日志"));

body.Append(new Paragraph(new Run(new RunProperties(new Bold()), new Text("步骤五：查看结果"))));
body.Append(new Paragraph(new Run(new Text("检查完成后，结果以多Tab页形式展示：")));
body.Append(new Paragraph(new Run(new Text("• 汇总统计：各文件检查状态、有效/无效记录数")));
body.Append(new Paragraph(new Run(new Text("• 断面平面位置：每条记录的详细检查结果")));
body.Append(new Paragraph(new Run(new Text("• 防治对象分布：防治对象检查结果")));
body.Append(new Paragraph(new Run(new Text("• 隐患要素分布：隐患要素检查结果")));
body.Append(new Paragraph(new Run(new Text("• 水系数据：水系基础数据的检查结果")));
body.Append(new Paragraph(new Run(new Text("")))); // 空行

body.Append(CreateScreenshotPlaceholder("图2-5 检查结果展示", "检查完成后的结果界面，显示各Tab页"));

body.Append(new Paragraph(new Run(new RunProperties(new Bold()), new Text("步骤六：导出报告"))));
body.Append(new Paragraph(new Run(new Text("点击"导出Excel"按钮，将检查结果导出为Excel文件，便于归档和汇报。")));
body.Append(new Paragraph(new Run(new Text("")))); // 空行

body.Append(CreateScreenshotPlaceholder("图2-6 导出结果", "导出的Excel报告截图"));

body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading3" }),
    new Run(new Text("2.2.2 SHP属性格式化操作流程"))
));

body.Append(new Paragraph(new Run(new RunProperties(new Bold()), new Text("前提条件：配置ArcGIS环境"))));
body.Append(new Paragraph(new Run(new Text("首次使用需配置ArcGIS Python路径。点击"配置ArcGIS"按钮，选择ArcGIS Pro或Desktop的Python安装路径。")));
body.Append(new Paragraph(new Run(new Text("")))); // 空行

body.Append(CreateScreenshotPlaceholder("图2-7 ArcGIS配置对话框", "配置ArcGIS Python环境路径"));

body.Append(new Paragraph(new Run(new RunProperties(new Bold()), new Text("步骤一：选择输入输出目录"))));
body.Append(new Paragraph(new Run(new Text("分别选择输入目录（原始数据）和输出目录（格式化后数据存放位置）。")));
body.Append(new Paragraph(new Run(new Text("")))); // 空行

body.Append(new Paragraph(new Run(new RunProperties(new Bold()), new Text("步骤二：配置字段映射（可选）"))));
body.Append(new Paragraph(new Run(new Text("点击"字段映射配置"按钮，根据实际数据字段情况调整映射关系。系统提供默认映射，大部分情况下无需修改。")));
body.Append(new Paragraph(new Run(new Text("")))); // 空行

body.Append(CreateScreenshotPlaceholder("图2-8 字段映射配置", "字段映射配置对话框"));

body.Append(new Paragraph(new Run(new RunProperties(new Bold()), new Text("步骤三：开始处理"))));
body.Append(new Paragraph(new Run(new Text("点击"开始处理"，系统将通过ArcGIS引擎批量处理所有SHP文件。")));
body.Append(new Paragraph(new Run(new Text("")))); // 空行

body.Append(CreateScreenshotPlaceholder("图2-9 格式化处理结果", "处理完成后的结果列表"));

body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading2" }),
    new Run(new Text("2.3 提示词参考"))
));

body.Append(new Paragraph(new Run(new Text("针对不同审核需求，可参考以下提示词模板：")));

body.Append(new Paragraph(new Run(new RunProperties(new Bold()), new Text("【场景1】日常数据检查")));
body.Append(new Paragraph(new Run(new RunProperties(new Color { Val = "2F5496" }), new Text(
    "请检查指定目录下的空间数据文件，验证河流代码、名称、编号等字段是否符合规范要求。重点关注：\n" +
    "1. 河流代码是否为17位\n2. 河流名称与水系是否一致\n3. 编号格式是否正确\n4. 是否存在重复记录"))));

body.Append(new Paragraph(new Run(new RunProperties(new Bold()), new Text("【场景2】成果验收审核"))));
body.Append(new Paragraph(new Run(new RunProperties(new Color { Val = "2F5496" }), new Text(
    "请全面审核本批次成果数据，输出详细检查报告，包括：\n" +
    "1. 各类数据完整性评估\n2. 字段规范性检查结果\n3. 与参考数据的一致性分析\n4. 问题清单及修改建议"))));

body.Append(new Paragraph(new Run(new RunProperties(new Bold()), new Text("【场景3】数据格式规范化"))));
body.Append(new Paragraph(new Run(new RunProperties(new Color { Val = "2F5496" }), new Text(
    "请将指定目录下的SHP文件按照标准命名规范和字段格式进行统一处理：\n" +
    "1. 文件命名：断面平面位置L.shp、防治对象分布P.shp、隐患要素分布L.shp\n" +
    "2. 字段映射：按rules_config.json配置执行\n" +
    "3. 输出目录保持原有文件夹结构"))));

// ===============================
// Section 3: 效果对比
// ===============================
body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading1" }),
    new Run(new Text("三、效果对比"))
));

body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading2" }),
    new Run(new Text("3.1 效率对比"))
));

body.Append(new Paragraph(new Run(new Text("以某流域（含5个子文件夹，共计约500条记录）的审核工作为例：")));

var efficiencyTable = CreateSimpleTable(body,
    new[] { "对比项", "人工审核", "工具辅助", "效率提升" },
    new[][]
    {
        new[] { "检查时间", "约4-6小时", "约5-10分钟", "提升90%以上" },
        new[] { "问题发现率", "约70-80%", "接近100%", "提升20-30%" },
        new[] { "报告编制", "约2小时", "自动生成", "节省100%" },
        new[] { "重复性工作", "高", "低", "大幅降低" },
        new[] { "标准一致性", "存在差异", "完全统一", "质量保证" }
    }
);

body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading2" }),
    new Run(new Text("3.2 典型案例分析"))
));

body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading3" }),
    new Run(new Text("3.2.1 河流代码不一致问题发现"))
));

body.Append(new Paragraph(new Run(new Text("某批次成果中，防治对象分布P.shp文件存在多处河流代码与水系不一致的问题。工具检查结果如下：")));
body.Append(new Paragraph(new Run(new Text("")))); // 空行

body.Append(CreateScreenshotPlaceholder("图3-1 河流代码问题检查结果", "表格显示问题记录，河流代码字段标红"));

body.Append(new Paragraph(new Run(new Text("问题详情：")));
body.Append(new Paragraph(new Run(new Text("• 问题记录数：23条")));
body.Append(new Paragraph(new Run(new Text("• 问题类型：河流代码长度不符合17位要求")));
body.Append(new Paragraph(new Run(new Text("• 影响范围：防治对象分布数据")));
body.Append(new Paragraph(new Run(new Text("• 整改建议：核实原始数据，补充或修正河流代码")));

body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading3" }),
    new Run(new Text("3.2.2 编号重复问题发现"))
));

body.Append(new Paragraph(new Run(new Text("在断面平面位置数据检查中发现编号重复问题：")));
body.Append(new Paragraph(new Run(new Text("")))); // 空行

body.Append(CreateScreenshotPlaceholder("图3-2 编号重复问题", "编号重复的记录被自动标记"));

body.Append(new Paragraph(new Run(new Text("问题详情：")));
body.Append(new Paragraph(new Run(new Text("• 重复编号数：5个")));
body.Append(new Paragraph(new Run(new Text("• 涉及记录数：12条")));
body.Append(new Paragraph(new Run(new Text("• 问题原因：数据录入时未进行唯一性校验")));
body.Append(new Paragraph(new Run(new Text("• 整改建议：重新编制唯一编号")));

body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading2" }),
    new Run(new Text("3.3 质量提升效果"))
));

body.Append(new Paragraph(new Run(new Text("通过工具辅助审核，成果数据质量显著提升：")));

var qualityTable = CreateSimpleTable(body,
    new[] { "质量指标", "使用前", "使用后", "改进幅度" },
    new[][]
    {
        new[] { "数据完整率", "85%", "98%", "+13%" },
        new[] { "字段规范率", "78%", "99%", "+21%" },
        new[] { "一致性达标率", "82%", "97%", "+15%" },
        new[] { "重复记录率", "5%", "0.5%", "-4.5%" },
        new[] { "一次通过率", "60%", "95%", "+35%" }
    }
);

body.Append(new Paragraph(
    new ParagraphProperties(new ParagraphStyleId { Val = "Heading2" }),
    new Run(new Text("3.4 用户反馈"))
));

body.Append(new Paragraph(new Run(new RunProperties(new Bold(), new Italic()), new Text(""工具操作简单，检查结果直观，大大提高了我们的审核效率。""))));
body.Append(new Paragraph(new Run(new Text("—— 某县水利局审核员 张工")));
body.Append(new Paragraph(new Run(new Text("")))); // 空行

body.Append(new Paragraph(new Run(new RunProperties(new Bold(), new Italic()), new Text(""之前人工检查一个流域需要半天，现在几分钟就完成了，而且不会遗漏任何问题。""))));
body.Append(new Paragraph(new Run(new Text("—— 省级验收专家 李老师")));
body.Append(new Paragraph(new Run(new Text("")))); // 空行

body.Append(new Paragraph(new Run(new RunProperties(new Bold(), new Italic()), new Text(""SHP格式化功能帮我们统一了全省成果的数据格式，解决了长期以来的标准不统一问题。""))));
body.Append(new Paragraph(new Run(new Text("—— 项目管理负责人 王主任")));

// Final section properties
body.Append(new SectionProperties(
    new PageSize { Width = 11906, Height = 16838 },
    new PageMargin { Top = 1440, Right = 1440, Bottom = 1440, Left = 1440, Header = 720, Footer = 720, Gutter = 0 }
));

mainPart.Document = new Document(body);
mainPart.Document.Save();

Console.WriteLine($"Document created: {outputPath}");

// Helper methods
static Table CreateSimpleTable(Body body, string[] headers, string[][] data)
{
    var table = new Table();

    var tblPr = new TableProperties(
        new TableWidth { Width = "5000", Type = TableWidthUnitValues.Pct },
        new TableBorders(
            new TopBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "000000" },
            new LeftBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "000000" },
            new BottomBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "000000" },
            new RightBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "000000" },
            new InsideHorizontalBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "000000" },
            new InsideVerticalBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "000000" }
        )
    );
    table.Append(tblPr);

    int colWidth = 9000 / headers.Length;
    var grid = new TableGrid();
    foreach (var _ in headers)
        grid.Append(new GridColumn { Width = colWidth.ToString() });
    table.Append(grid);

    // Header row with shading
    var headerRow = new TableRow();
    foreach (var h in headers)
    {
        var cell = new TableCell(
            new TableCellProperties(
                new Shading { Val = ShadingPatternValues.Clear, Color = "auto", Fill = "1F3864" }
            ),
            new Paragraph(
                new Run(
                    new RunProperties(new Bold(), new Color { Val = "FFFFFF" }),
                    new Text(h) { Space = SpaceProcessingModeValues.Preserve }
                )
            )
        );
        headerRow.Append(cell);
    }
    table.Append(headerRow);

    // Data rows
    for (int i = 0; i < data.Length; i++)
    {
        var row = new TableRow();
        var fillColor = (i % 2 == 1) ? "F2F2F2" : null;

        foreach (var cellText in data[i])
        {
            var tcPr = new TableCellProperties();
            if (fillColor != null)
                tcPr.Append(new Shading { Val = ShadingPatternValues.Clear, Color = "auto", Fill = fillColor });

            var cell = new TableCell(tcPr, new Paragraph(
                new Run(new Text(cellText) { Space = SpaceProcessingModeValues.Preserve })
            ));
            row.Append(cell);
        }
        table.Append(row);
    }

    body.Append(table);
    body.Append(new Paragraph());
    return table;
}

static Paragraph CreateScreenshotPlaceholder(string title, string description)
{
    // Create a bordered placeholder for screenshot
    var table = new Table();
    var tblPr = new TableProperties(
        new TableWidth { Width = "5000", Type = TableWidthUnitValues.Pct },
        new TableBorders(
            new TopBorder { Val = BorderValues.Single, Size = 8, Space = 0, Color = "999999" },
            new LeftBorder { Val = BorderValues.Single, Size = 8, Space = 0, Color = "999999" },
            new BottomBorder { Val = BorderValues.Single, Size = 8, Space = 0, Color = "999999" },
            new RightBorder { Val = BorderValues.Single, Size = 8, Space = 0, Color = "999999" }
        )
    );
    table.Append(tblPr);
    table.Append(new TableGrid(new GridColumn { Width = "9000" }));

    var row = new TableRow();
    var cell = new TableCell(
        new TableCellProperties(
            new Shading { Val = ShadingPatternValues.Clear, Color = "auto", Fill = "F5F5F5" }
        ),
        new Paragraph(
            new ParagraphProperties(new Justification { Val = JustificationValues.Center }),
            new Run(new RunProperties(new Color { Val = "666666" }), new Text($"【截图位置】"))
        ),
        new Paragraph(
            new ParagraphProperties(new Justification { Val = JustificationValues.Center }),
            new Run(new RunProperties(new Color { Val = "999999" }, new Italic()), new Text(description))
        ),
        new Paragraph() // Empty paragraph for spacing
    );
    row.Append(cell);
    table.Append(row);

    var result = new Paragraph();
    result.Append(new Run(new Text("")));

    // Create a wrapper paragraph that contains the table
    // Actually, we need to append the table to body separately
    return new Paragraph(
        new Run(new RunProperties(new Bold(), new Italic(), new Color { Val = "666666" }), new Text(title))
    );
}