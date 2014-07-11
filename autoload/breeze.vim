" autoload/breeze.vim


" Init
" ----------------------------------------------------------------------------

let s:current_folder = expand("<sfile>:p:h")

fu! breeze#init()
    py import vim, sys
    py sys.path.insert(0, vim.eval("s:current_folder"))
    py import breeze.core
    py breeze_plugin = breeze.core.Breeze()
endfu

call breeze#init()
let g:breeze_initialized = 1

" Wrappers
" ----------------------------------------------------------------------------

" tag jumping

fu! breeze#JumpForward()
    py breeze_plugin.jump_forward()
endfu

fu! breeze#JumpBackward()
    py breeze_plugin.jump_backward()
endfu

" tag matching / highlighting

fu! breeze#MatchTag()
    py breeze_plugin.match_tag()
endfu

fu! breeze#HighlightElement()
    py breeze_plugin.highlight_curr_element()
endfu

" dom navigation

fu! breeze#NextSibling()
    py breeze_plugin.goto_next_sibling()
endfu

fu! breeze#PrevSibling()
    py breeze_plugin.goto_prev_sibling()
endfu

fu! breeze#FirstSibling()
    py breeze_plugin.goto_first_sibling()
endfu

fu! breeze#LastSibling()
    py breeze_plugin.goto_last_sibling()
endfu

fu! breeze#FirstChild()
    py breeze_plugin.goto_first_child()
endfu

fu! breeze#LastChild()
    py breeze_plugin.goto_last_child()
endfu

fu! breeze#Parent()
    py breeze_plugin.goto_parent()
endfu

" misc

fu! breeze#PrintDom()
    py breeze_plugin.print_dom()
endfu

fu! breeze#WhatsWrong()
    py breeze_plugin.whats_wrong()
endfu


" Autocommands
" ----------------------------------------------------------------------------

py import breeze.utils.v

augroup breeze_plugin
    au!

    exe 'au Colorscheme '.g:breeze_active_filetypes.' py breeze_plugin.setup_colors()'
    exe 'au CursorMoved,CursorMovedI,BufLeave,BufWinLeave,WinLeave *.* py breeze.utils.v.clear_hl("BreezeHl")'

    exe 'au BufReadPost,BufWritePost,BufEnter '.g:breeze_active_filetypes.' py breeze_plugin.refresh_cache=True'
    exe 'au CursorHold,CursorHoldI '.g:breeze_active_filetypes.' py breeze_plugin.refresh_cache=True'
    exe 'au InsertEnter,InsertLeave '.g:breeze_active_filetypes.' py breeze_plugin.refresh_cache=True'
    exe 'au BufWritePost '.g:breeze_active_filetypes.' py breeze_plugin.refresh_cache=True'

    if g:breeze_highlight_curr_element
        exe 'au CursorMoved '.g:breeze_active_filetypes.' py breeze_plugin.highlight_curr_element()'
        au InsertEnter *.* py breeze.utils.v.clear_hl("BreezeHl")
    endif

augroup END
