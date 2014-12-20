""" Test module to parse xprotocl text
"""

from os.path import join as pjoin, dirname

import xpparse as xpp

from nose.tools import (assert_true, assert_false, assert_equal,
                        assert_not_equal, assert_raises)


DATA_PATH = dirname(__file__)
EG_PROTO = pjoin(DATA_PATH, 'xprotocol_sample.txt')

LEXER = xpp.get_lexer()

def to_comparable(parse_results, expected):
    if hasattr(expected, 'keys'):
        out = {}
        for k, v in parse_results.items():
            out[k] = to_comparable(v, expected[k])
        return out
    elif isinstance(expected, list):
        out = []
        assert_equal(len(parse_results), len(expected))
        for v, ex_v in zip(parse_results, expected):
            out.append(to_comparable(v, ex_v))
        return out
    return parse_results


def assert_tokens(source, expected):
    LEXER.input(source)
    assert_equal([t.value for t in LEXER], expected)


def assert_parsed(source, start, expected):
    parser = xpp.get_parser(start)
    assert_equal(parser.parse(source), expected)


def test_strings_newlines():
    assert_tokens('"A string"', ['A string'])
    assert_tokens('"A ""string"', ['A ""string'])
    assert_tokens('"A multi\n\nline\n\nlong string with\n""Double quotes"""',
                  ['A multi\n\nline\n\nlong string with\n""Double quotes""'])


def test_tags():
    assert_tokens('<xprotocol>', ['xprotocol'])
    assert_tokens('<XProtocol>', ['XProtocol'])
    assert_tokens(' <ParamLong."Count"> ', ['Count'])
    assert_tokens('<ParamBool."IsInlineComposed">', ['IsInlineComposed'])
    assert_tokens('<ParamMap."">', [''])
    assert_tokens('<ParamCardLayout."Inline Compose">', ['Inline Compose'])


def test_lines_and_so_on():
    assert_parsed('<Line>  { 126 48 126 140 }',
                  'line',
                  [126, 48, 126, 140])
    assert_parsed("""
                  <Line>  { 126 48 126 140 }
                  <Line>  { 276 48 276 140 }
                  """,
                  'lines',
                  [[126, 48, 126, 140], [276, 48, 276, 140]])
    assert_parsed('<Repr> "LAYOUT_10X2_WIDE_CONTROLS"',
                  'repr',
                  "LAYOUT_10X2_WIDE_CONTROLS")
    assert_parsed('<Param> "MultiStep.IsInlineCompose"',
                  'param',
                  "MultiStep.IsInlineCompose")
    assert_parsed('<Pos> 110 48',
                  'pos',
                  [110, 48])
    assert_parsed('<Pos> 110 48',
                  'pos',
                  [110, 48])
    assert_parsed('<Control>  { <Param> "MultiStep.ComposingFunction" '
                  '<Pos> 77 63 }',
                  'control',
                  dict(param="MultiStep.ComposingFunction",
                       pos=[77, 63],
                       repr=None))
    assert_parsed('<Control>  { <Param> "MultiStep.IsInlineCompose" '
                  '<Pos> 110 48 <Repr> "UI_CHECKBOX" }',
                  'control',
                  dict(param="MultiStep.IsInlineCompose",
                       pos=[110, 48],
                       repr="UI_CHECKBOX"))
    assert_parsed("""
    <Control>  { <Param> "MultiStep.IsInlineCompose" <Pos> 110 48 <Repr> "UI_CHECKBOX" }
    <Control>  { <Param> "MultiStep.ComposingFunction" <Pos> 77 63 }
    <Control>  { <Param> "MultiStep.ComposingGroup" <Pos> 77 78 }
    <Control>  { <Param> "MultiStep.IsLastStep" <Pos> 110 93 <Repr>
                  "UI_CHECKBOX" }""",
                  'controls',
                  [dict(param="MultiStep.IsInlineCompose",
                        pos=[110, 48],
                        repr="UI_CHECKBOX"),
                   dict(param="MultiStep.ComposingFunction",
                        pos=[77, 63],
                        repr=None),
                   dict(param="MultiStep.ComposingGroup",
                        pos=[77, 78],
                        repr=None),
                   dict(param="MultiStep.IsLastStep",
                        pos=[110, 93],
                        repr="UI_CHECKBOX")])


def test_param_card():
    assert_parsed("""
  <ParamCardLayout."Inline Compose">
  {
    <Repr> "LAYOUT_10X2_WIDE_CONTROLS"
    <Control>  { <Param> "MultiStep.IsInlineCompose" <Pos> 110 48 <Repr> "UI_CHECKBOX" }
    <Control>  { <Param> "MultiStep.ComposingFunction" <Pos> 77 63 }
    <Control>  { <Param> "MultiStep.ComposingGroup" <Pos> 77 78 }
    <Control>  { <Param> "MultiStep.IsLastStep" <Pos> 110 93 <Repr> "UI_CHECKBOX" }
    <Line>  { 126 48 126 140 }
    <Line>  { 276 48 276 140 }
  }""",
                  'param_card_layout',
                  dict(type='param_card_layout',
                       name='Inline Compose',
                       repr="LAYOUT_10X2_WIDE_CONTROLS",
                       controls=[
                           dict(param="MultiStep.IsInlineCompose",
                                pos=[110, 48],
                                repr="UI_CHECKBOX"),
                           dict(param="MultiStep.ComposingFunction",
                                pos=[77, 63],
                                repr=None),
                           dict(param="MultiStep.ComposingGroup",
                                pos=[77, 78],
                                repr=None),
                           dict(param="MultiStep.IsLastStep",
                                pos=[110, 93],
                                repr="UI_CHECKBOX")],
                  lines=[[126, 48, 126, 140], [276, 48, 276, 140]]))


def test_context_and_so_on():
    assert_parsed('<Context> "ONLINE"', 'context', 'ONLINE')
    assert_parsed('<Dll> "MrMultiStepDependencies"',
                  'dll',
                  "MrMultiStepDependencies")
    assert_parsed('<Class> "PipeLinkService@MrParc"',
                  'class',
                  "PipeLinkService@MrParc")
    assert_parsed('<Dependency."Value_FALSE"> {"AlwaysFalse" }',
                  'dependency',
                  dict(type='dependency',
                       name='Value_FALSE',
                       values=['AlwaysFalse'],
                       dll=None,
                       context=None))
    assert_parsed('<Dependency."MrMS_DH_TIMCT"> '
                  '{"MultiStep.IsInlineCompose" '
                  '<Dll> "MrMultiStepDependencies" '
                  '<Context> "ONLINE" }',
                  'dependency',
                  dict(type='dependency',
                       name="MrMS_DH_TIMCT",
                       values=["MultiStep.IsInlineCompose"],
                       dll="MrMultiStepDependencies",
                       context="ONLINE"))
    assert_parsed('<Dependency."1_Availability"> '
                  '{"MultiStep.IsMultistep" "MultiStep.SubStep" '
                  '"MultiStep.IsInlineCombine" <Context> "ONLINE" }',
                  'dependency',
                  dict(type='dependency',
                       name="1_Availability",
                       values=["MultiStep.IsMultistep",
                               "MultiStep.SubStep",
                               "MultiStep.IsInlineCombine"],
                       dll=None,
                       context="ONLINE"))


def test_scalars():
    # bools, ints, floats, strings
    assert_tokens('"true"', [True])
    assert_tokens('"false"', [False])
    assert_tokens('12', [12])
    assert_tokens('-12', [-12])
    assert_tokens('22.3', [22.3])
    assert_tokens('12 "true" 22.3 "false" "string"',
                  [12, True, 22.3, False, 'string'])
    assert_parsed('22.3', 'scalar', 22.3)
    assert_parsed('221', 'scalar', 221)
    assert_parsed('-221', 'scalar', -221)
    assert_parsed('"true"', 'scalar', True)
    assert_parsed('"false"', 'scalar', False)


def test_lists():
    assert_parsed('22.3 12.3', 'float_list', [22.3, 12.3])
    assert_parsed('22 12', 'integer_list', [22, 12])
    assert_parsed('"22" "12"', 'string_list', ['22', '12'])


def test_key_value():
    # Key value pair, where value can be a list
    assert_parsed('<name> 22.3', 'key_value', ('name', 22.3))
    assert_parsed('<name> 22', 'key_value', ('name', 22))
    assert_parsed('<name> "string"', 'key_value', ('name', 'string'))
    assert_parsed('<name> {22 23}', 'key_value', ('name', [22, 23]))


def test_attr_list():
    # Attr list is a list of key_value or tagged params
    assert_parsed("""<Label> "Inline Composing"
                  <Tooltip> "Invokes Inline Composing."
                  <Another> 10
                  """,
                  'attr_list',
                  [('Label', 'Inline Composing'),
                   ('Tooltip', 'Invokes Inline Composing.'),
                   ('Another', 10)])
    assert_parsed("""<Label> "Inline Composing"
                  <Tooltip> "Invokes Inline Composing."
                  <LimitRange> { "false" "true" }
                  <Another> 10
                  """,
                  'attr_list',
                  [('Label', 'Inline Composing'),
                   ('Tooltip', 'Invokes Inline Composing.'),
                   ('LimitRange', [False, True]),
                   ('Another', 10)])
    assert_parsed('   ', 'attr_list', [])


def test_param_blocks():
    # Test parameter blocks
    assert_parsed("""<ParamBool."IsInlineComposed">
                  {
                  <LimitRange> { "false" "true" }
                 }
                  """,
                  'param_bool',
                  dict(type='param_bool',
                       name='IsInlineComposed',
                       attrs=[('LimitRange', [False, True])],
                       value=None))
    assert_parsed("""<ParamBool."IsInlineComposed">
                  {
                  <LimitRange> { "false" "true" }
                  "true"
                 }
                  """,
                  'param_bool',
                  dict(type='param_bool',
                       name='IsInlineComposed',
                       attrs=[('LimitRange', [False, True])],
                       value=True))
    assert_parsed(""" <ParamLong."Count">
                  {
                  1
                 }""",
                  'param_long',
                  dict(type='param_long',
                       name='Count',
                       attrs=[],
                       value=1))
    assert_parsed('<Default> <ParamLong.""> { }',
                  'param_long',
                  dict(type='param_long',
                       name='',
                       attrs=[],
                       value=None))
    assert_parsed('<Default> <ParamLong.""> { }',
                  'block',
                  dict(type='param_long',
                       name='',
                       attrs=[],
                       value=None))
    assert_parsed('<ParamString."GROUP">  { "Calculation"  }',
                  'param_string',
                  dict(type='param_string',
                       name='GROUP',
                       attrs=[],
                       value='Calculation'))
    assert_parsed("""<ParamString."GROUP">
                  {
                  <Default> <ParamLong."">
                  {
                  }
                  "Calculation"
                 }
                  """,
                  'param_string',
                  dict(type='param_string',
                       name='GROUP',
                       attrs=[('Default', dict(type='param_long',
                                               name='',
                                               attrs=[],
                                               value=None))],
                       value='Calculation'))


def test_param_array():
    assert_parsed("""<ParamArray."EstimatedDuration">
                  {
                  <MinSize> 1
                  <MaxSize> 1000000000
                  <Default> <ParamLong."">
                  {
                 }
                  { 450 200 }
                 }""",
                  'param_array',
                  dict(type='param_array',
                       name='EstimatedDuration',
                       attrs=[('MinSize', 1),
                              ('MaxSize', 1000000000),
                              ('Default', dict(type='param_long',
                                               name='',
                                               attrs=[],
                                               value=None))],
                        value=[450, 200]))
    assert_parsed("""
                  <ParamArray."BValue">
                  {
                  <Default> <ParamLong."">
                  {
                 }
                  { }
                 }""",
                  'param_array',
                  dict(type='param_array',
                       name='BValue',
                       attrs=[('Default', dict(type='param_long',
                                               name='',
                                               attrs=[],
                                               value=None))],
                       value=[]))


def test_param_map():
    assert_parsed("""<ParamMap."">
                  {

                  <ParamBool."IsInlineComposed">
                  {
                  <LimitRange> { "false" "true" }
                 }

                  <ParamLong."Count">
                  {
                  1
                 }
                 }""",
                  'param_map',
                  dict(type='param_map',
                       name='',
                       value=[dict(type='param_bool',
                                   name='IsInlineComposed',
                                   attrs=[('LimitRange', [False, True])],
                                   value=None),
                              dict(type='param_long',
                                   name='Count',
                                   attrs=[],
                                   value=1)]))


def test_param_choice():
    assert_parsed("""
      <ParamChoice."ComposingFunction">
      {
        <Label> "Composing Function"
        <Tooltip> "Defines the composing algorithm to be used."
        <Default> "Angio"
        <Limit> { "Angio" "Spine" "Adaptive" }
      }""",
                  'param_choice',
                  dict(type='param_choice',
                       name='ComposingFunction',
                       attrs=[('Label', 'Composing Function'),
                              ('Tooltip', 'Defines the composing algorithm '
                               'to be used.'),
                              ('Default', 'Angio'),
                              ('Limit', ['Angio', 'Spine', 'Adaptive'])]))


def test_event():
    assert_parsed('<Event."ImageReady">  { "int32_t" "class IceAs &" '
                  '"class MrPtr<class MiniHeader,class Parc::Component> &" '
                  '"class ImageControl &" }',
                  'event',
                  dict(type='event',
                       name='ImageReady',
                       args=["int32_t",
                             "class IceAs &",
                             "class MrPtr<class MiniHeader,"
                             "class Parc::Component> &",
                             "class ImageControl &"]))


def test_method():
    assert_parsed('<Method."ComputeImage">  { "int32_t" "class IceAs &" '
                  '"class MrPtr<class MiniHeader,class Parc::Component> &" '
                  '"class ImageControl &"  }',
                  'method',
                  dict(type='method',
                       name='ComputeImage',
                       args = ["int32_t",
                               "class IceAs &",
                               "class MrPtr<class MiniHeader,"
                               "class Parc::Component> &",
                               "class ImageControl &"]))


def test_connection():
    assert_parsed('<Connection."c1">  { '
                  '"ImageReady" '
                  '"DtiIcePostProcMosaicDecorator" '
                  '"ComputeImage"  }',
                  'connection',
                  dict(type='connection',
                       name='c1',
                       args=["ImageReady",
                             "DtiIcePostProcMosaicDecorator",
                             "ComputeImage"]))
    assert_parsed('<Connection."c1">  { "ImageReady" "" "ComputeImage"  }',
                  'connection',
                  dict(type='connection',
                       name='c1',
                       args=["ImageReady",
                             "",
                             "ComputeImage"]))


def test_class():
    assert_parsed('<Class> "MosaicUnwrapper@IceImagePostProcFunctors"',
                  'class',
                  "MosaicUnwrapper@IceImagePostProcFunctors")


def test_emc():
    assert_parsed("""
<Event."ImageReady">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
<Method."ComputeImage">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
<Connection."c1">  { "ImageReady" "DtiIcePostProcMosaicDecorator" "ComputeImage"  } """,
                  'emc',
                  [dict(type='event',
                        name='ImageReady',
                        args=["int32_t",
                              "class IceAs &",
                              "class MrPtr<class MiniHeader,"
                              "class Parc::Component> &",
                              "class ImageControl &"]),
                   dict(type='method',
                        name='ComputeImage',
                        args=["int32_t",
                              "class IceAs &",
                              "class MrPtr<class MiniHeader,"
                              "class Parc::Component> &",
                              "class ImageControl &"]),
                   dict(type='connection',
                        name='c1',
                        args=["ImageReady",
                              "DtiIcePostProcMosaicDecorator",
                              "ComputeImage"])])


def test_functor():
    assert_parsed("""
<ParamFunctor."MosaicUnwrapper">
{
<Class> "MosaicUnwrapper@IceImagePostProcFunctors"

<ParamBool."EXECUTE">  { }
<Event."ImageReady">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
<Method."ComputeImage">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
<Connection."c1">  { "ImageReady" "DtiIcePostProcMosaicDecorator" "ComputeImage"  }
}""",
                  'param_functor',
                  {'type': 'param_functor',
                   'name': 'MosaicUnwrapper',
                   'class': "MosaicUnwrapper@IceImagePostProcFunctors",
                   'value': [dict(type='param_bool',
                                  name='EXECUTE',
                                  attrs=[],
                                  value=None)],
                   'event': dict(
                       type='event',
                       name='ImageReady',
                       args=["int32_t",
                             "class IceAs &",
                             "class MrPtr<class MiniHeader,"
                             "class Parc::Component> &",
                             "class ImageControl &"]),
                   'method': dict(
                       type='method',
                       name='ComputeImage',
                       args=["int32_t",
                             "class IceAs &",
                             "class MrPtr<class MiniHeader,"
                             "class Parc::Component> &",
                             "class ImageControl &"]),
                   'connection': dict(
                       type='connection',
                       name='c1',
                       args=["ImageReady",
                             "DtiIcePostProcMosaicDecorator",
                             "ComputeImage"])})


def test_pipe_service():
    # Smoke test to see if we can parse a pipe service
    parser = xpp.get_parser('pipe_service')
    res = parser.parse(
        """
    <PipeService."EVA">
    {
      <Class> "PipeLinkService@MrParc"

      <ParamLong."POOLTHREADS">  { 1  }
      <ParamString."GROUP">  { "Calculation"  }
      <ParamLong."DATATHREADS">  { }
      <ParamLong."WATERMARK">  { 16  }
      <ParamString."tdefaultEVAProt">  { "%SiemensEvaDefProt%/DTI/DTI.evp"  }
      <ParamFunctor."MosaicUnwrapper"> 
      {
        <Class> "MosaicUnwrapper@IceImagePostProcFunctors" 

        <ParamBool."EXECUTE">  { }
        <Event."ImageReady">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
        <Method."ComputeImage">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
        <Connection."c1">  { "ImageReady" "" "ComputeImage"  }
      }
      <ParamFunctor."DtiIcePostProcFunctor"> 
      {
        <Class> "DtiIcePostProcFunctor@DtiIcePostProc" 

        <ParamBool."EXECUTE">  { "true"  }
        <ParamArray."BValue"> 
        {
          <Default> <ParamLong.""> 
          {
          }
          { }

        }
        <ParamLong."Threshold">  { 40  }
        <ParamLong."NoOfDirections4FirstBValue">  { }
        <ParamLong."ScalingFactor">  { 1  }
        <ParamLong."UpperBound">  { }
        <ParamLong."Threshold4AutoLoadInViewer">  { 400  }
        <ParamLong."DiffusionMode">  { }
        <ParamBool."DiffWeightedImage">  { "true"  }
        <ParamBool."ADCMap">  { }
        <ParamBool."AverageADCMap">  { "true"  }
        <ParamBool."TraceWeightedImage">  { "true"  }
        <ParamBool."FAMap">  { "true"  }
        <ParamBool."Anisotropy">  { }
        <ParamBool."Tensor">  { }
        <ParamBool."E1">  { }
        <ParamBool."E2">  { }
        <ParamBool."E3">  { }
        <ParamBool."E1-E2">  { }
        <ParamBool."E1-E3">  { }
        <ParamBool."E2-E3">  { }
        <ParamBool."VR">  { }
        <ParamLong."bValueforADC">  { }
        <ParamBool."bValueforADCCheckbox">  { }
        <ParamBool."InvertGrayScale">  { }
        <ParamBool."ExponentialADCMap">  { "true"  }
        <ParamBool."CalculatedImage">  { }
        <ParamLong."CalculatedbValue">  { 1400  }
        <ParamBool."RA">  { }
        <ParamBool."Linear">  { }
        <ParamBool."Planar">  { }
        <ParamBool."Spherical">  { }
        <ParamBool."IsInlineProcessing">  { "true"  }
        <Method."ComputeImage">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
        <Event."ImageReady">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
        <Connection."c1">  { "ImageReady" "DtiIcePostProcMosaicDecorator" "ComputeImage"  }
      }
      <ParamFunctor."DtiIcePostProcMosaicDecorator"> 
      {
        <Class> "DtiIcePostProcMosaicDecorator@DtiIcePostProc" 
        
        <ParamBool."EXECUTE">  { "true"  }
        <ParamBool."Mosaic">  { "true"  }
        <ParamBool."MosaicDiffusionMaps">  { }
        <Event."ImageReady">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
        <Method."ComputeImage">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
        <Connection."connection0">  { "ImageReady" "imagesend_ps.imagesend" "ComputeImage"  }
      }
      <ParamBool."WIPFlagSetbySequenceDeveloper">  { }
    }""")
    assert_equal(res['name'], 'EVA')


def test_eva_string_table():
    assert_parsed("""
  <EVAStringTable>
  {
    34
    400 "Multistep Protocol"
    401 "Step"
    447 "Adaptive"
  }""",
                  'eva_string_table',
                  ('EVAStringTable',
                   (34, [(400, "Multistep Protocol"),
                         (401, "Step"),
                         (447, "Adaptive")])))


def test_xp_hdr():
    assert_parsed("""<Name> "PhoenixMetaProtocol"
                  <ID> 1000002
                  <Userversion> 2.0""",
                  'xp_hdr',
                  dict(Name="PhoenixMetaProtocol",
                       ID=1000002,
                       Userversion=2.0))


def test_depends():
    assert_parsed('<Dependency."Value_FALSE"> {"AlwaysFalse" } '
                  '<Dependency."1_Availability"> '
                  '{"MultiStep.IsMultistep" "MultiStep.SubStep" '
                  '"MultiStep.IsInlineCombine" <Context> "ONLINE" }',
                  'depends',
                  [dict(type='dependency',
                       name='Value_FALSE',
                       values=['AlwaysFalse'],
                       dll=None,
                       context=None),
                  dict(type='dependency',
                       name="1_Availability",
                       values=["MultiStep.IsMultistep",
                               "MultiStep.SubStep",
                               "MultiStep.IsInlineCombine"],
                       dll=None,
                       context="ONLINE")])
    assert_parsed('', 'depends', [])


def test_xprotocol():
    # Smoke test to see if we can parse an xprotocol
    parser = xpp.get_parser('xprotocol')
    res = parser.parse("""
<XProtocol>
{
  <Name> "PhoenixMetaProtocol"
  <ID> 1000002
  <Userversion> 2.0

  <ParamMap."">
  {

    <ParamBool."IsInlineComposed">
    {
      <LimitRange> { "false" "true" }
    }

    <ParamLong."Count">
    {
      1
    }
  }
}""")
    assert_equal(res,
                 dict(type='xprotocol',
                      Name="PhoenixMetaProtocol",
                      ID=1000002,
                      Userversion=2.0,
                      blocks=[dict(type='param_map',
                                  name='',
                                  value=[dict(type='param_bool',
                                              name='IsInlineComposed',
                                              attrs=[('LimitRange',
                                                      [False, True])],
                                              value=None),
                                         dict(type='param_long',
                                              name='Count',
                                              attrs=[],
                                              value=1)])],
                      cards=[],
                      depends=[]))


def test_sample_file():
    with open(EG_PROTO, 'rt') as fobj:
        contents = fobj.read()
    parser = xpp.get_parser()
    res = parser.parse(contents)
    assert_equal(len(res), 1)
    protocol = res[0]
    assert_equal(len(protocol['depends']), 0)
    assert_equal(len(protocol['blocks']), 1)
    for v in protocol['blocks'][0]['value']:
        if v['name'].startswith('Protocol'):
            break
    proto_str = xpp.split_ascconv(xpp.strip_twin_quote(v['value']))[0]
    res2 = parser.parse(proto_str)
    assert_equal(len(res2), 2)
