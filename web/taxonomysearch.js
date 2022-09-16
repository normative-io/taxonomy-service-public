// Copyright 2022 Meta Mind AB
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

const blackCircle = '&nbsp;&#9679;&nbsp; ';
const openCircle = '&#9678; ';
const noCircle = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ';
const leafmarker = noCircle;

function endpoint(operation) {
  return host + '/taxonomy/' + taxonomy + (version ? '/' + version : '') + '/' + operation;
}

function taxonomysearch(next) {
  status('Downloading ' + taxonomy + ' data');
  $('#tree').addClass('hidden');

  $.get(endpoint('tree'), (data, err) => {
    (async () => {
      await status('Building tree');
      buildtree($('#tree'), data.tree);

      await status('Making it interactive');
      JSLists.applyToList('tree', 'ALL');

      await status('Rendering');
      $('#tree').removeClass('hidden');

      await status('');

      $('#tree')
        .find('li > div')
        .click(function (e, w, f) {
          $(this).parent().find('li.hidden').removeClass('hidden');
          if (
            $(this).filter('.jsl-list-open').length > 0 &&
            $(this).siblings('ul.jsl-open').length == 0
          ) {
            // toggle this partially open node to be open
            $(this).siblings('ul').addClass('jsl-open');
            // open partially hidden subtrees below this node
            $(this)
              .siblings('ul')
              .find('ul.jsl-open')
              .siblings('div')
              .addClass('jsl-list-open');
          }
        });

      $('#tree')
        .find('li')
        .mousedown(function (ev) {
          $('#code').val(this.id);
          $('#name').val(this.getAttribute('name'));
          $('#metadata').val(this.getAttribute('metadata'));
          $('.selected').removeClass('selected');
          $(this).addClass('selected');
          ev.stopPropagation();

          const prevY = window.scrollY;
          window.location.hash = this.id;
          window.scroll(window.scrollX, prevY);
        })
        .dblclick(function (ev) {
          if (ev.target.nodeName == 'LI' && ev.target.children.length > 0) {
            if (
              !ev.target.children[0].classList.contains('jsl-list-open') &&
              ev.target.children[1].classList.contains('jsl-open')
            ) {
              ev.target.children[1].classList.toggle('jsl-open');
            }

            ev.target.children[0].classList.toggle('jsl-list-open');
            ev.target.children[1].classList.toggle('jsl-open');
            $(ev.target.children[1]).children().removeClass('hidden');

            ev.stopPropagation();
          }
        });
      if (next) next();
    })().then(() => { });
  });
}

const sleep = (milliseconds) => {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
};

async function status(s) {
  $('#status').text(s);
  await sleep(1);
}

function buildtree(tree_el, tree) {
  if (!tree || tree.length == 0) return;

  // Build a subtree
  let subtree_el = $('<ul>');
  tree.sort((a, b) => (a.name < b.name ? -1 : 1));

  for (const branch of tree) {
    let branch_el = $('<li>');
    branch_el.attr('id', branch.id);
    branch_el.attr('name', branch.name);
    metadata = JSON.stringify(branch.metadata);
    branch_el.attr('metadata', metadata);

    if (metadata) {
      branch_el.addClass('selectable');
    } else {
      branch_el.addClass('unselectable');
    }

    if (branch.children && branch.children.length > 0) {
      branch_el.append('<div>');
    } else {
      branch_el.append(leafmarker);
    }
    branch_el.append(branch.name);
    branch_el.attr('title', branch.id);
    buildtree(branch_el, branch.children);
    subtree_el.append(branch_el);
  }
  tree_el.append(subtree_el);
}

function showel(el) {
  el.parents('ul').addClass('jsl-open');
  el.parents('li.hidden').removeClass('hidden');
  el.removeClass('hidden');
}

function collapseall(tree) {
  tree.find('ul.jsl-open').removeClass('jsl-open');
  tree.find('dev.jsl-list-open').removeClass('jsl-list-open');
}

function hideall(tree) {
  tree.find('li.highlighted').css('background', '').removeClass('highlighted');
}

function score2rgb(score) {
  score = Math.min(1, Math.max(0, score));
  return [1 - 0.2 * score, 1, 1 - 0.3 * score];
}

function rgb2css([r, g, b]) {
  const toint = (x) => Math.min(255, Math.max(0, Math.round(255 * x)));
  const css = `rgb(${toint(r)}, ${toint(g)}, ${toint(b)})`;
  return css;
}

function idselector(id) {
  return `[id='${id}']`;
}

$('#filter').keyup(function (ev) {
  let query = '' + this.value;
  if (query === '') {
    collapseall($('#tree'));
    return;
  }

  searchid(query, (matches) => {
    const tree = $('#tree');
    collapseall(tree);
    hideall(tree);

    if (0 < matches.length) {
      let els = tree.find(matches.map((x) => idselector(x.id)).join(','));
      els
        .add(els.parents('li'))
        .siblings()
        .addClass('hidden')
        .find('div.jsl-list-open')
        .removeClass('jsl-list-open');
      $('.jslist > ul > li').removeClass('hidden');
      showel(els);
    }

    // Adjust background of all selected elements
    for (const m of matches) {
      $(idselector(m.id))
        .css('background', rgb2css(score2rgb(m.score)))
        .addClass('highlighted');
    }
  });
});

function searchid(query, cb) {
  if (window.lastquery == '' + query) return;
  window.lastquery = '' + query;
  $.get(endpoint('search') + '?query=' + query,
    (data, err) => {
      if (err === 'success' && query === window.lastquery) cb(data.matches);
    },
  );
}

function markcode(code) {
  let el = $(idselector(code));
  showel(el);

  $('#name').val(el.attr('name'));
  $('#metadata').val(el.attr('metadata'));
  $('.selected').removeClass('selected');
  el.addClass('selected');
  return el;
}

function showsibling(el) {
  let oldtop = el.offset().top - window.scrollY;

  // show siblings
  el.parent().siblings('div').addClass('jsl-list-open');
  el.siblings().removeClass('hidden');

  // show children
  el.children('ul').addClass('jsl-open');
  el.children('ul').children().removeClass('hidden');
  el.children('div').addClass('jsl-list-open');

  window.scroll(window.scrollX, el.offset().top - oldtop);
}

function findel(code) {
  let el = markcode(code);
  if (el.length > 0) {
    showsibling(el);

    el.addClass('scrolltarget');
    document
      .querySelector('.scrolltarget')
      .scrollIntoView({ behavior: 'smooth' });
    el.removeClass('scrolltarget');
  }
}

function readhash() {
  if (window.location.hash !== '') {
    const code = window.location.hash.slice(1);
    if (code != $('#code').val()) {
      $('#code').val(code).focus();
      findel(code);
    }
  }
}

$('#code').keyup(function (ev) {
  if (ev.keyCode == 13) {
    let code = '' + this.value;
    const prevY = window.scrollY;
    window.location.hash = code;
    window.scroll(window.scrollX, prevY);
    findel(code);
  }
});
