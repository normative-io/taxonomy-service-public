/*
 Based on JSLists by George Duff
*/

/*
 *	JSLists v0.4.5
 *	© 2016 George Duff
 *
 * 	Release date: 01/06/2016
 *	The MIT License (MIT)
 *	Copyright (c) 2016 George Duff
 *	Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
 *	The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
 *	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */

//	TO DO LIST - Will get round to most of them at some point!
//	Add folder & file icons dynamically from param
//	Collapse All & Open All are ropey at best!
//	Add a search function
//	Make the margins user definable
//	Add support for UL & OL

(function () {
  'use strict';
  function define_JSLists() {
    var JSLists = {};

    const clickSublistevent = function (e) {
      e.target.classList.toggle('jsl-list-open');
      e.target.parentElement.lastElementChild.classList.toggle('jsl-open');
      e.stopPropagation();
    };

    JSLists.createTree = function (listId) {
      const tree = document.getElementById(listId);
      let listItems = tree.getElementsByTagName('LI');

      for (let i = 0; i < listItems.length; i++) {
        const curElem = listItems[i];

        if (curElem.children.length > 0) {
          const tglDiv = curElem.children[0]; // first one should be a DIV
          const tglUl = curElem.children[1]; // second should be an UL
          tglUl.setAttribute('class', 'jsl-collapsed');
          tglDiv.setAttribute('class', 'jsl-list-closed');
          tglDiv.setAttribute('id', listItems[i].id + i + '_tgl');

          document
            .getElementById(listItems[i].id + i + '_tgl')
            .addEventListener('click', clickSublistevent, true);
        }
      }
    };

    JSLists.applyToList = function (listId, bulletPoint) {
      document.getElementById(listId).style.display = 'none;';

      this.createTree(listId);

      setTimeout(function () {
        document.getElementById(listId).style.display = 'block;';
      }, 50); // stops FOUC!
    };
    return JSLists;
  }

  //define the JSLists library in the global namespace if it doesn't already exist
  if (typeof JSLists === 'undefined') {
    window.JSLists = define_JSLists();
  } else {
    console.log('JSLists already defined.');
  }
})();
