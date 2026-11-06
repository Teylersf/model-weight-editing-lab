import { buildMethodLibrary, openMethodLibrary } from './library.mjs';

const [command, ...args] = process.argv.slice(2);

try {
  let result;
  if (command === 'build' && !args.length) {
    result = buildMethodLibrary();
  } else if (['search', 'resolve', 'show', 'coverage'].includes(command)) {
    const library = openMethodLibrary();
    try {
      if (command === 'search') result = library.search({ query: args.join(' ') });
      if (command === 'resolve') result = library.resolve({ name: args.join(' ') });
      if (command === 'show' && args.length === 1) result = library.get(args[0]);
      if (command === 'coverage' && !args.length) {
        result = { revision: library.revision, searchRevision: library.searchRevision, coverage: library.coverage() };
      }
    } finally {
      library.close();
    }
  }
  if (result === undefined) throw new Error('Use npm run math -- build | search "your problem" | resolve "method name" | show method-id | coverage');
  console.log(JSON.stringify(result, null, 2));
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
