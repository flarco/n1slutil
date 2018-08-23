# General Helpers Lib
import datetime
import json
import logging
import os
import re
import sys
from collections import namedtuple, OrderedDict
from decimal import Decimal
from pathlib import Path

import dateutil

try:
  from colorama import Fore, Back, Style
  color_enabled = True
except ImportError:
  color_enabled = False

try:
  import halo
  Status = halo.Halo
  status = Status(text='', spinner='dots')
except ImportError:
  Status = None
  status = None

### LAMBDAS ############################

get_rec = lambda row, headers: struct({h.lower():row[i] for i,h in enumerate(headers)})
now = lambda: datetime.datetime.now()
now_str = lambda: datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
now_file_str = lambda: datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
today_str = lambda: datetime.datetime.now().strftime('%Y%m%d')
get_row_fields = lambda r: r._fields if hasattr(r, '_fields') else r.__fields__
jdumps = lambda obj: json.dumps(obj, cls=MyJSONEncoder)
is_gen_func = lambda x: str(x).startswith('<generator ')
get_profile = lambda: load_profile()
get_kw = lambda k, deflt, kwargs: kwargs[k] if k in kwargs else deflt

get_script_path = lambda: os.path.dirname(os.path.realpath(sys.argv[0]))
get_dir_path = lambda f=__file__: os.path.dirname(f)
file_exists = lambda p: Path(p).exists()

elog = lambda text, show_time=True: log(text, color='red', show_time=show_time)
slog = lambda text, show_time=True: log(text, color='green', show_time=show_time)

## LOGGING ############################

# Create a logger object.
logger = logging.getLogger(__name__)

try:
  # https://pypi.org/project/coloredlogs/
  # https://coloredlogs.readthedocs.io/en/latest/api.html#changing-the-log-format
  os.environ[
    'COLOREDLOGS_LOG_FORMAT'] = '[%(hostname)s] %(asctime)s %(levelname)s | %(message)s'
  os.environ['COLOREDLOGS_LOG_FORMAT'] = '%(asctime)s | %(message)s'

  import coloredlogs
  # By default the install() function installs a handler on the root logger,
  # this means that log messages from your code and log messages from the
  # libraries that you use will all show up on the terminal.
  # coloredlogs.install(level='DEBUG')

  # If you don't want to see log messages from libraries, you can pass a
  # specific logger object to the install() function. In this case only log
  # messages originating from that logger will show up on the terminal.
  coloredlogs.install(level='DEBUG', logger=logger)

  def log(text, color='white', level='INFO', **kwargs):
    level = 'ERROR' if color == 'red' else level
    level = 'WARNING' if color == 'yellow' else level
    level = 'SUCCESS' if color == 'green' else level

    if isinstance(text, Exception):
      level = 'ERROR'
      error = text
      try:
        raise (error)
      except:
        text = get_exception_message()

    if level == 'ERROR':
      logger.error(text)
    elif level == 'WARNING':
      logger.warning(text)
    elif level == 'DEBUG':
      logger.debug(text)
    # elif level == 'SUCCESS':
    #   logger.success(text)
    else:
      logger.info(text)

  elog = lambda text, show_time=True: log(text, level='ERROR', show_time=show_time)
  slog = lambda text, show_time=True: log(text, level='SUCCESS', show_time=show_time)

except:

  def log(text, color='white', show_time=True, new_line=True, use_halo=False):
    """Print to stdout"""
    new_line = False if use_halo else new_line

    if color_enabled:
      time_str = now_str() + Fore.MAGENTA + ' -- ' if show_time else ''
      color_map = dict(
        red=Fore.RED,
        blue=Fore.BLUE,
        green=Fore.GREEN,
        yellow=Fore.YELLOW,
        magenta=Fore.MAGENTA,
        white=Fore.WHITE,
      )
      line = '{}{}{}'.format(
        time_str, color_map[color.lower()] + str(text) + Style.RESET_ALL, '\n'
        if new_line else '')
    else:
      time_str = now_str() + ' -- ' if show_time else ''
      line = '{}{}{}'.format(time_str, text, '\n' if new_line else '')

    if use_halo:
      # status.start()
      status.text = line
      # status.stop()
    else:
      sys.stdout.write(line)
      sys.stdout.flush()

  elog = lambda text, show_time=True: log(text, color='red', show_time=show_time)
  slog = lambda text, show_time=True: log(text, color='green', show_time=show_time)


def get_exception_message(append_message='', raw=False):
  """Returns the exception message as a formatted string"""
  import linecache
  import traceback

  exc_type, exc_obj, tb = sys.exc_info()
  f = tb.tb_frame
  lineno = tb.tb_lineno
  filename = f.f_code.co_filename
  linecache.checkcache(filename)
  line = linecache.getline(filename, lineno, f.f_globals)
  message = '-' * 65 + '\n' + 'EXCEPTION IN ({}, LINE {} "{}"): {} \n---\n{}'.format(
    filename, lineno, line.strip(), exc_obj,
    traceback.format_exc()) + '\n' + append_message
  if raw: message = str(exc_obj)
  return message


time_start = now()


def get_elapsed_time(time_start=time_start):
  time_end = datetime.datetime.now()
  delta_time = divmod(
    (time_end - time_start).days * 86400 + (time_end - time_start).seconds, 60)
  return str(delta_time[0]) + ' mins ' + str(
    delta_time[1]) + ' seconds elapsed'


pprogress_stdt = now()
pprogress_updt = now()
pprogress_i = 1000


def pprogress(i, total, sec_intvl=0.2, text='Complete', show_time=True):
  "Print loop progress"
  global pprogress_updt, pprogress_stdt, pprogress_i
  pp = lambda: sys.stderr.write('\r{:,.1f}% [{} / {}] {}'.format(100.0*(i)/total, i, total, text))
  if i < pprogress_i:
    pprogress_stdt = now()

  if i == total:
    pp()
    print('')
    if show_time: print(get_elapsed_time(pprogress_stdt))
  elif (now() - pprogress_updt).total_seconds() > sec_intvl:
    pp()
    pprogress_updt = now()
  pprogress_i = i


def ptable(headers, rows, format='string', table=None):
  from prettytable import PrettyTable
  if table:
    table.clear_rows()
  else:
    table = PrettyTable(headers)

  for row in rows:
    table.add_row(row)

  return table.get_string()


### Profile ############################

from xutil.diskio import read_yaml


def load_profile():
  if not os.getenv('PROFILE_YAML'):
    raise Exception("Env Var PROFILE_YAML is not set!")

  dict_ = read_yaml(os.getenv('PROFILE_YAML'))
  if 'environment' in dict_:
    for key in dict_['environment']:
      os.environ[key] = dict_['environment'][key]

  return dict_


def get_variables():
  dd = get_profile()
  return dd['variables'] if 'variables' in dd else {}


def get_databases():
  dd = get_profile()
  return dd['databases'] if 'databases' in dd else {}


def get_db_profile(db_name):
  dbs = get_databases()
  if db_name in dbs:
    return struct(dbs[db_name])
  else:
    raise Exception("Could not find Database '{}' in profile.".format(db_name))


## CLASSES & DATA OPS ##########################


class struct(dict):
  """ Dict with attributes getter/setter. """

  def __getattr__(self, name):
    return self[name]

  def __setattr__(self, name, value):
    self[name] = value


class MyJSONEncoder(json.JSONEncoder):
  def default(self, o):
    if isinstance(o, datetime.datetime) or isinstance(o, datetime.date):
      # return o.isoformat()
      return str(o)
    elif isinstance(o, bytes):
      return o.decode(errors='ignore')
    elif isinstance(o, Decimal):
      return float(o)
    try:
      val = json.JSONEncoder.default(self, o)
    except:
      val = str(o)
    return val


def str_format(text, data, enc_char):
  """This takes a text template, and formats the encapsulated occurences with data keys
  Example: if text = 'My name is $$name$$', provided data = 'Bob' and enc_char = '$$'.
    the returned text will be 'My name is Bob'.
  """
  for key in data:
    val = data[key]
    text = text.replace('{}{}{}'.format(enc_char, str(key), enc_char),
                        str(val))
  return text


def str_rmv_indent(text):
  """This removes the indents from a string"""
  # return text
  if not text: return text
  matches = list(re.finditer(r'^ *', text.strip(), re.MULTILINE))
  if not matches: return text
  min_indent = min([len(m.group()) for m in matches])
  regex = r"^ {" + str(min_indent) + r"}"
  new_text = re.sub(regex, '', text, 0, re.MULTILINE)
  return new_text


def split(data, split_size):
  """Yield successive split_size-sized chunks from data (list or dataframe)."""
  if isinstance(data, list):
    for i in range(0, len(data), split_size):
      yield data[i:i + split_size]
  else:
    for i in range(0, len(data), split_size):
      yield data.iloc[i:i + split_size]


def isnamedtupleinstance(x):
  t = type(x)
  b = t.__bases__
  if len(b) != 1 or b[0] != tuple: return False
  f = getattr(t, '_fields', None)
  if not isinstance(f, tuple): return False
  return all(type(n) == str for n in f)


class DictTree:
  def __init__(self, data, header_only=False, name_processor=None):
    self.data = data
    self.name_processor = name_processor
    self.get_keys_path(header_only=header_only)
    self.TRow = namedtuple(
      'TRow',
      'title action field_name field_type depth_level field_path is_null is_list len'
    )

  def get_keys_path(self, header_only=False):
    "Traverses nested dictionary and returns depth level and corresponding JMESPath search string"
    # http://jmespath.org/specification.html#examples
    # https://github.com/jmespath/jmespath.py
    from pyspark.sql import Row
    fields_parent = OrderedDict()
    DP = namedtuple('DictPath', 'level key path vtype field_name')
    name_processor = self.name_processor if self.name_processor else None

    def get_data_type(val):
      if isinstance(val, dict): return 'dict'
      if isinstance(val, list): return 'list'
      try:
        float(val)
        return 'number'
      except:
        try:
          dateutil.parser.parse(val)
          return 'datetime'
        except:
          return 'string'

    def get_field_name(key, parent):
      prefix = ''
      parent = parent.replace('"', '')

      if (parent.endswith('[*]') and len(parent.split('.')) > 1) or \
          (parent.endswith('[*]') and not parent.startswith('[*]')):
        prefix = parent.replace('[*]', '').split('.')[-1] + '_'

      if name_processor:
        prefix = name_processor(prefix)
        key = name_processor(key)

      f_name_new = f_name = prefix + key
      i = 0
      while f_name_new in fields_parent and fields_parent[f_name_new] != parent:
        i += 1
        f_name_new = f_name + str(i)
      fields_parent[f_name_new] = parent
      return f_name_new

    q = lambda s: '"' + s + '"'

    def get_paths(d1, level=1, parent=''):
      kks = set()

      if isinstance(d1, dict):
        if "Header" in d1:
          keys = ["Header"] + [k for k in d1 if k != "Header"]
        else:
          keys = list(d1)
        for key in keys:
          if key.startswith('@'): continue
          vt = get_data_type(d1[key])
          field_name = get_field_name(
            key, parent) if vt not in ('dict', 'list') else None
          path = '{}{}'.format(parent + '.' if parent else '', q(key))
          kks.add(DP(level, key, path, vt, field_name))
          kks = kks.union(get_paths(d1[key], level=level + 1, parent=path))
          if header_only and key == "Header": return kks
      elif isinstance(d1, list):
        key = '[*]'
        path = '{}{}'.format(parent if parent else '', key)
        if level == 1:
          vt = get_data_type(d1)
          kks.add(DP(level, key, path, vt, None))
        for item in d1:
          vt = get_data_type(item)
          kks = kks.union(get_paths(item, level=level + 1, parent=path))

      return kks

    self.paths = sorted(get_paths(self.data))
    self.v_paths = [r for r in self.paths if r.vtype not in ('dict', 'list')]
    self.v_lists = [r for r in self.paths if r.vtype in ('list')]
    self.fields = [
      r.field_name for r in self.paths if r.vtype not in ('dict', 'list')
    ]
    self.fields_dict = {
      r.field_name: r
      for r in self.paths if r.vtype not in ('dict', 'list')
    }
    self.Rec = Row(*self.fields)

    try:
      self.title = list(self.data)[0]
      self.action = self.get_value('Action', conv_date=False)
    except:
      pass

    return self.paths

  def search(self, path):
    from jmespath import search
    return search(path, self.data)

  def get_value(self, field, conv_date=True):
    val = self.search(self.fields_dict[field].path)
    if conv_date and self.fields_dict[field].vtype == 'date':
      try:
        val = dateutil.parser.parse(val)
      except:
        pass
    return val

  def get_field_table(self):
    "Create fields table"
    t_rows = []
    for field in self.fields:
      val = self.get_value(field)
      rec = dict(
        title=self.title,
        action=self.action,
        field_name=field,
        field_type=self.fields_dict[field].vtype,
        depth_level=self.fields_dict[field].level,
        field_path=self.fields_dict[field].path,
        is_null=0 if str(val).strip() else 1,
        is_list=1 if isinstance(val, list) else 0,
        len=len(str(val)),
      )

      t_rows.append(self.TRow(**rec))
    return t_rows

  def get_record(self):
    "Returns one record, omitting lists N:N relationships"
    return self.Rec(*[self.get_value(f) for f in self.fields])