export function verificationRedirectError(value){
  const url=new URL(value);
  const query=url.searchParams;
  const fragment=new URLSearchParams(url.hash.replace(/^#/,''));
  const code=fragment.get('error_code')||query.get('error_code');
  const error=fragment.get('error')||query.get('error');
  if(!code&&!error)return '';
  if(code==='bad_oauth_state')
    return 'That Google sign-in attempt expired. Return to OneThing and choose Continue with Google again; an old sign-in link cannot be reused.';
  return code==='otp_expired'
    ? 'That verification link expired. Enter your email and request a new link.'
    : 'We could not complete sign-in or verify that email link. Please try again.';
}
