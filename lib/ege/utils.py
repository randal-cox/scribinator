import pprint, datetime, shutil, os
from typing import List, Any, Union, Optional

def format_elapsed_time(secs: Union[int, float]) -> str:
  """Standard way to format elapsed time"""
  ret = str(datetime.timedelta(seconds=int(secs))).split(':')
  ret = list(zip([r for r in ret], ['h', 'm', 's']))

  # find the first non-zero entry
  ret_non_zero = [i for i in range(len(ret)) if ret[i][0] not in ['0', '00']]
  if len(ret_non_zero) == 0: return "0s"

  idx = ret_non_zero[0]
  ret = ' '.join(f"{int(r[0])}{r[1]}" for r in ret[idx:])
  return ret

def pp(*args: Union[Any, ...], as_string: bool = False) -> Optional[str]:
  """
    Convenience method to pretty print stuff. Just say
      pp(args)
  """
  if len(args) == 1: args = args[0]
  if as_string:
    return pprint.pformat(args, indent=2, width=120)
  else:
    return pprint.PrettyPrinter(indent=2, width=120).pprint(args)

def recursive_copy(src_dir: str, dst_dir: str, ignore_items: List[str]) -> None:
  """Convenience to recursively copy src_dir to dst_dir, but omitting some items

     :param src_dir: The source directory from which to copy.
     :param dst_dir: The destination directory where the content should be copied.
     :param ignore_items: A list of files or directories to be excluded during the copying process.

     Usage example:
       recursive_copy('/path/to/src_dir', '/path/to/dst_dir', ['ignore_dir', 'ignore_file.txt'])
     """
  if not os.path.exists(dst_dir): os.makedirs(dst_dir)

  for item in os.listdir(src_dir):
    if item in ignore_items: continue
    s = os.path.join(src_dir, item)
    d = os.path.join(dst_dir, item)

    if os.path.isdir(s):
      recursive_copy(s, d, ignore_items)
    else:
      shutil.copy2(s, d)

def remove_extension(path):
  """I remove the extension of a file so often, I wanted a convenience method"""
  return os.path.splitext(path)[0]

def greek_letters(num: int) -> str:
  """Simple converter of integers to greek letter names - useful for some default names"""

  greek_alphabet = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta",
                    "eta", "theta", "iota", "kappa", "lambda", "mu",
                    "nu", "xi", "omicron", "pi", "rho", "sigma",
                    "tau", "upsilon", "phi", "chi", "psi", "omega"]
  quotient, remainder = divmod(num, len(greek_alphabet))
  return greek_alphabet[remainder] + (str(quotient) if quotient > 0 else "")