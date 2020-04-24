import styled from 'styled-components'
import React, { Component } from 'react'
import AceEditor from 'react-ace'
import 'brace/theme/idle_fingers'
import 'brace/mode/python'
import 'brace/snippets/python'
import 'brace/ext/language_tools'
import PropTypes from 'prop-types'
import { withTheme } from '@material-ui/core/styles'
import RunCodeButton from 'components/RunCodeButton'
import { connect } from 'react-redux'
import { actions as editorActions } from 'features/Editor'
import Editor from '@monaco-editor/react'
// import doEditorStuff from './monacoCode'

// doEditorStuff()

export const IDEEditorLayout = styled.div`
  position: relative;
  grid-area: ide-editor;
`

export const PositionedRunCodeButton = styled(RunCodeButton)`
  && {
    position: absolute;
    right: ${props => props.theme.spacing(3)}px;
    bottom: ${props => props.theme.spacing(3)}px;
    z-index: 5;
  }
`

export class IDEEditor extends Component {
  constructor (props) {
    super(props)
    this.state = {
      code: '// type your code...'
    }
  }

  editorDidMount (editor) {
    // console.log('got here')
    this.editor = editor
    // console.log(editor)
    this.props.getCode()
    editor.onDidChangeModelContent(ev => {
      // console.log(this.editor.getValue())
      this.props.editorChanged(this.editor.getValue())
    })
  }

  isCodeOnServerDifferent () {
    return this.props.code !== this.props.codeOnServer
  }

  options () {
    return {
      enableBasicAutocompletion: true,
      enableLiveAutocompletion: true,
      enableSnippets: true,
      showLineNumbers: true,
      tabSize: 4,
      fontFamily: this.props.theme.additionalVariables.typography.code
        .fontFamily
    }
  }

  render () {
    const code = this.state.code
    // console.log(this.props.code)
    return (
      <IDEEditorLayout>
        <Editor
          language='python'
          theme='dark'
          value={this.props.code}
          options={{
            codeLens: false,
            showLineNumbers: true,
            contextmenu: false,
            minimap: {
              enabled: false
            }
          }}
          forwardRef={ref => (this.editorRef = ref)}
          // onChange={this.props.editorChanged}
          editorDidMount={(_, editor) => this.editorDidMount(editor)}
        />
        {/* <AceEditor
          mode='python'
          theme='idle_fingers'
          name='ace_editor'
          onLoad={this.props.getCode}
          onChange={this.props.editorChanged}
          fontSize={this.props.theme.additionalVariables.typography.code.fontSize}
          showPrintMargin
          showGutter
          highlightActiveLine
          value={this.props.code}
          width='100%'
          height='100%'
          setOptions={this.options()}
        /> */}
        <PositionedRunCodeButton
          runCodeButtonStatus={this.props.runCodeButtonStatus}
          isCodeOnServerDifferent
          aria-label='Run Code'
          id='post-code-button'
          whenClicked={() => this.props.postCode(this.state.code)}
        />
      </IDEEditorLayout>
    )
  }
}

IDEEditor.propTypes = {
  code: PropTypes.string,
  codeOnServer: PropTypes.string,
  getCode: PropTypes.func,
  editorChanged: PropTypes.func,
  theme: PropTypes.object,
  postCode: PropTypes.func,
  runCodeButtonStatus: PropTypes.object
}

const mapStateToProps = state => ({
  code: state.editor.code.code,
  codeOnServer: state.editor.code.codeOnServer,
  runCodeButtonStatus: state.editor.runCodeButton
})

const mapDispatchToProps = {
  getCode: editorActions.getCodeRequest,
  editorChanged: editorActions.keyPressed,
  postCode: editorActions.postCodeRequest
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withTheme(IDEEditor))
