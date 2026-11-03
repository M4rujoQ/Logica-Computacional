import marimo
 
__generated_with = "0.25.2"
app = marimo.App()
 
 
@app.cell
def _():
    import marimo as mo
 
    return (mo,)
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Exercício 3 — Multiplicação de inteiros com um SFOTS em BitVec
 
    **Convenções**
 
    - Os inteiros são vetores de bits de tamanho $n$ (nos testes, $n = 8$), tratados **sem sinal**: usamos `BVULT`, `BVLShl`, `BVLShr` e `BVZExt`.
    - O `pc` é um inteiro que identifica o nodo do CFA: `INIT=0, SKIP=1, LEFT=2, RIGHT=3, STOP=4, ERROR=5`.
    - Em Z3 a aritmética de `BitVec` é módulo $2^n$ e nunca falha, por isso o overflow tem de ser detetado explicitamente no modelo.
    - As verificações pedem sempre ao solver um **contra-exemplo**: `UNSAT` significa que a condição vale.
    """)
    return
 
 
@app.cell
def _():
    from pysmt.shortcuts import (Symbol, And, Or, Not, Implies, Ite, Equals, NotEquals,
                                 Int, BV, BVAnd, BVAdd, BVSub, BVMul, BVULT, BVLShl,
                                 BVLShr, BVExtract, BVZExt, Solver)
    from pysmt.typing import INT, BVType
 
    return (
        And,
        BV,
        BVAdd,
        BVAnd,
        BVExtract,
        BVLShl,
        BVLShr,
        BVMul,
        BVSub,
        BVType,
        BVULT,
        BVZExt,
        Equals,
        INT,
        Implies,
        Int,
        Ite,
        Not,
        NotEquals,
        Or,
        Solver,
        Symbol,
    )
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## 1. Construção do SFOTS
 
    ### Variáveis de estado
 
    | variável | tipo | papel |
    |---|---|---|
    | `pc` | `INT` | nodo do CFA |
    | `a`, `b` | `BitVec(n)` | inputs (constantes ao longo da execução) |
    | `x`, `y`, `z` | `BitVec(n)` | variáveis do algoritmo |
 
    `a` e `b` fazem parte do estado porque o invariante $x*y + z = a*b$ precisa dos valores **iniciais**, que `x` e `y` vão perdendo. Como cada cópia do estado tem símbolos novos (`a0, a1, ...`), o solver não sabe que representam a mesma quantidade. Por isso a relação de transição impõe `a' = a` e `b' = b` (função `same`), o que as torna constantes em qualquer traço.
    """)
    return
 
 
@app.cell
def _(BV, BVType, INT, Symbol):
    # Número de bits (parâmetro do programa)
    N = 8
 
    # Identificadores dos nodos do CFA (valores do pc)
    INIT, SKIP, LEFT, RIGHT, STOP, ERROR = 0, 1, 2, 3, 4, 5
 
 
    def bv(v):
        '''Constante BitVec de N bits.'''
        return BV(v, N)
 
 
    def declare(i):
        '''i-ésima cópia das variáveis de estado.'''
        state = {}
        state['pc'] = Symbol('pc' + str(i), INT)
        state['a'] = Symbol('a' + str(i), BVType(N))
        state['b'] = Symbol('b' + str(i), BVType(N))
        state['x'] = Symbol('x' + str(i), BVType(N))
        state['y'] = Symbol('y' + str(i), BVType(N))
        state['z'] = Symbol('z' + str(i), BVType(N))
        return state
 
    return ERROR, INIT, LEFT, N, RIGHT, SKIP, STOP, bv, declare
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Funções auxiliares
 
    - **Paridade.** `par(y)` é `BVAnd(y, 1) = 0`: o `AND` com a máscara `00…01` isola o bit menos significativo, que decide a paridade.
    - **Overflow de $x \ll 1$.** Há perda de informação se e só se o bit mais significativo de `x` é 1, isto é, $x \geq 2^{n-1}$.
    - **Overflow de $z + x$.** A soma dá a volta se e só se o resultado fica menor que `z`: `BVULT(z + x, z)`.
    - **`same`** impõe que as variáveis indicadas ficam iguais entre o estado atual e o seguinte.
    """)
    return
 
 
@app.cell
def _(And, BV, BVAdd, BVAnd, BVExtract, BVULT, Equals, N, Not, bv):
    def even(y):
        return Equals(BVAnd(y, bv(1)), bv(0))
 
 
    def odd(y):
        return Not(even(y))
 
 
    def overflow_left(s):
        # x << 1 perde o bit mais significativo de x
        return Equals(BVExtract(s['x'], N - 1, N - 1), BV(1, 1))
 
 
    def overflow_right(s):
        # z + x dá "carry" (em unsigned o resultado fica menor que um dos operandos)
        return BVULT(BVAdd(s['z'], s['x']), s['z'])
 
 
    def same(curr, prox, names):
        '''As variáveis em 'names' mantêm o valor.'''
        return And([Equals(prox[v], curr[v]) for v in names])
 
    return even, odd, overflow_left, overflow_right, same
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Estado inicial
 
    $$
    \mathit{init}(s) \;\equiv\; pc = \mathit{INIT} \,\wedge\, x = a \,\wedge\, y = b \,\wedge\, z = 0
    $$
 
    Optámos por o estado inicial já ter `x, y, z = a, b, 0`, em vez de 0. Assim o invariante $x*y + z = a*b$ vale logo no estado inicial. O nodo `INIT` mantém-se, como no diagrama, e a transição `init → skip` repete a atribuição (que já está satisfeita). Não se impõe nenhuma restrição sobre `a` e `b`, para verificar o programa para todas as entradas.
    """)
    return
 
 
@app.cell
def _(And, Equals, INIT, Int, bv):
    def init(s):
        # arranca no nodo init; a e b são os inputs (sem restrições por agora)
        # e já temos x = a, y = b, z = 0
        return And(Equals(s['pc'], Int(INIT)),
                   Equals(s['x'], s['a']),
                   Equals(s['y'], s['b']),
                   Equals(s['z'], bv(0)))
 
    return (init,)
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Relação de transição
 
    | transição | guarda | efeito |
    |---|---|---|
    | `init → skip` | — | $x,y,z \leftarrow a,b,0$ |
    | `skip → left` | $y \neq 0 \wedge \mathit{par}(y)$ | só muda o `pc` |
    | `skip → right` | $y \neq 0 \wedge \mathit{impar}(y)$ | só muda o `pc` |
    | `skip → stop` | $y = 0$ | só muda o `pc` |
    | `left → skip` | $\neg \mathit{ovf}_{\ll}(x)$ | $x \leftarrow x \ll 1,\; y \leftarrow y \gg 1$ |
    | `left → error` | $\mathit{ovf}_{\ll}(x)$ | só muda o `pc` |
    | `right → skip` | $\neg \mathit{ovf}_{+}(z,x)$ | $y \leftarrow y - 1,\; z \leftarrow z + x$ |
    | `right → error` | $\mathit{ovf}_{+}(z,x)$ | só muda o `pc` |
    | `stop → stop`, `error → error` | — | ciclo (todo o estado tem sucessor) |
 
    - **Precedência do erro.** A transição normal só é possível quando não há overflow e a de erro só quando há: as guardas são mutuamente exclusivas.
    - **`y >> 1` e `y - 1`** não precisam de teste de overflow: só se aplicam com `y` par (`y >> 1` não perde nenhum bit 1) e com `y` ímpar (`y - 1 ≥ 0`).
    """)
    return
 
 
@app.cell
def _(
    And,
    BVAdd,
    BVLShl,
    BVLShr,
    BVSub,
    ERROR,
    Equals,
    INIT,
    Int,
    LEFT,
    Not,
    NotEquals,
    Or,
    RIGHT,
    SKIP,
    STOP,
    bv,
    even,
    odd,
    overflow_left,
    overflow_right,
    same,
):
    def trans(c, p):
        # a e b são constantes ao longo da execução
        ab = same(c, p, ['a', 'b'])
 
        # init -> skip : x,y,z <- a,b,0
        t_init = And(Equals(c['pc'], Int(INIT)), Equals(p['pc'], Int(SKIP)),
                     Equals(p['x'], c['a']), Equals(p['y'], c['b']),
                     Equals(p['z'], bv(0)))
 
        # skip -> left / right / stop (só escolhem o ramo, não alteram x,y,z)
        xyz = same(c, p, ['x', 'y', 'z'])
        t_skip_left = And(Equals(c['pc'], Int(SKIP)), NotEquals(c['y'], bv(0)),
                          even(c['y']), Equals(p['pc'], Int(LEFT)), xyz)
        t_skip_right = And(Equals(c['pc'], Int(SKIP)), NotEquals(c['y'], bv(0)),
                           odd(c['y']), Equals(p['pc'], Int(RIGHT)), xyz)
        t_skip_stop = And(Equals(c['pc'], Int(SKIP)), Equals(c['y'], bv(0)),
                          Equals(p['pc'], Int(STOP)), xyz)
 
        # left -> skip : x,y,z <- 2*x, y/2, z   (se não houver overflow)
        t_left = And(Equals(c['pc'], Int(LEFT)), Not(overflow_left(c)),
                     Equals(p['pc'], Int(SKIP)),
                     Equals(p['x'], BVLShl(c['x'], bv(1))),
                     Equals(p['y'], BVLShr(c['y'], bv(1))),
                     Equals(p['z'], c['z']))
        # left -> error (o erro tem precedência)
        t_left_err = And(Equals(c['pc'], Int(LEFT)), overflow_left(c),
                         Equals(p['pc'], Int(ERROR)), xyz)
 
        # right -> skip : x,y,z <- x, y-1, z+x   (se não houver overflow)
        t_right = And(Equals(c['pc'], Int(RIGHT)), Not(overflow_right(c)),
                      Equals(p['pc'], Int(SKIP)),
                      Equals(p['x'], c['x']),
                      Equals(p['y'], BVSub(c['y'], bv(1))),
                      Equals(p['z'], BVAdd(c['z'], c['x'])))
        # right -> error
        t_right_err = And(Equals(c['pc'], Int(RIGHT)), overflow_right(c),
                          Equals(p['pc'], Int(ERROR)), xyz)
 
        # stop e error ficam em ciclo (todo o estado tem sucessor)
        t_stop = And(Equals(c['pc'], Int(STOP)), Equals(p['pc'], Int(STOP)), xyz)
        t_err = And(Equals(c['pc'], Int(ERROR)), Equals(p['pc'], Int(ERROR)), xyz)
 
        return And(ab, Or(t_init, t_skip_left, t_skip_right, t_skip_stop,
                          t_left, t_left_err, t_right, t_right_err,
                          t_stop, t_err))
 
    return (trans,)
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Estado de erro
 
    $$
    \mathit{erro}(s) \;\equiv\; pc = \mathit{ERROR}
    $$
    """)
    return
 
 
@app.cell
def _(ERROR, Equals, Int):
    def error(s):
        return Equals(s['pc'], Int(ERROR))
 
    return (error,)
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Validação do modelo
 
    A função `gera_traco` pede ao solver um traço de `k` estados que respeite `init` e `trans`. O parâmetro `extra` permite escolher o cenário.
    """)
    return
 
 
@app.cell
def _(Solver):
    def gera_traco(declare, init, trans, k, extra=None):
        with Solver(name="z3") as s:
            states = [declare(i) for i in range(k)]
            s.add_assertion(init(states[0]))
            for i in range(k - 1):
                s.add_assertion(trans(states[i], states[i + 1]))
            if extra is not None:
                s.add_assertion(extra(states))
            if s.solve():
                for i, st in enumerate(states):
                    vals = {v: s.get_value(st[v]) for v in st}
                    print(f"Estado {i}: " + ", ".join(f"{v}={vals[v]}" for v in vals))
            else:
                print("Nenhum traço encontrado")
 
    return (gera_traco,)
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Com $a = 3,\, b = 5$ o traço percorre `init → skip → right → skip → left → … → stop` e termina com $z = 15 = 3 \times 5$.
    """)
    return
 
 
@app.cell
def _(And, Equals, bv, declare, gera_traco, init, trans):
    gera_traco(declare, init, trans, 12,
               extra=lambda S: And(Equals(S[0]['a'], bv(3)), Equals(S[0]['b'], bv(5))))
    return
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Com $a = 100,\, b = 3$ forçamos o último estado a ser de erro: em `right`, com $x = 200$ e $z = 100$, a soma $300$ não cabe em 8 bits e o programa vai para `error`.
    """)
    return
 
 
@app.cell
def _(And, Equals, bv, declare, error, gera_traco, init, trans):
    gera_traco(declare, init, trans, 12,
               extra=lambda S: And(Equals(S[0]['a'], bv(100)), Equals(S[0]['b'], bv(3)), error(S[-1])))
    return
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## 2. Verificação de $x*y + z = a*b$ por $k$-indução
 
    $$
    \varphi(s) \;\equiv\; x*y + z = a*b \qquad\text{(em } \texttt{BitVec}(n)\text{, módulo } 2^n\text{)}
    $$
 
    ### Método
 
    A $k$-indução prova $G\,\varphi$ com duas verificações:
 
    - **Base:** $\varphi$ vale nos primeiros $k$ estados de qualquer traço que comece num estado inicial. Procura-se $\mathit{init}(s_0) \wedge \mathit{trans}(s_0,s_1) \wedge \dots \wedge \bigvee_i \neg\varphi(s_i)$.
    - **Passo:** se $\varphi$ vale em $k$ estados consecutivos, vale no seguinte. Procura-se $\bigwedge_{i<k}\big(\varphi(s_i) \wedge \mathit{trans}(s_i,s_{i+1})\big) \wedge \neg\varphi(s_k)$.
 
    Com $k = 1$ é a indução simples.
    """)
    return
 
 
@app.cell
def _(Not, Or, Solver):
    def mostra(states, model):
        for i, st in enumerate(states):
            print(f"  Estado {i}: " + ", ".join(f"{v}={model.get_value(st[v])}" for v in st))
 
 
    def kinduction_always(declare, init, trans, inv, k, verbose=True):
        '''Verifica G inv por k-indução. Devolve True se base e passo valem.'''
        # --- base: inv vale nos primeiros k estados de qualquer traço inicial ---
        with Solver(name="z3") as s:
            S = [declare(i) for i in range(k)]
            s.add_assertion(init(S[0]))
            for i in range(k - 1):
                s.add_assertion(trans(S[i], S[i + 1]))
            s.add_assertion(Or([Not(inv(st)) for st in S]))
            if s.solve():
                if verbose:
                    print(f"k={k}: a BASE falha. Contra-exemplo:")
                    mostra(S, s.get_model())
                return False
 
        # --- passo: inv em k estados consecutivos => inv no seguinte ---
        with Solver(name="z3") as s:
            S = [declare(i) for i in range(k + 1)]
            for i in range(k):
                s.add_assertion(inv(S[i]))
                s.add_assertion(trans(S[i], S[i + 1]))
            s.add_assertion(Not(inv(S[k])))
            if s.solve():
                if verbose:
                    print(f"k={k}: o PASSO falha. Contra-exemplo:")
                    mostra(S, s.get_model())
                return False
 
        if verbose:
            print(f"k={k}: invariante verificado por {k}-indução.")
        return True
 
    return kinduction_always, mostra
 
 
@app.cell
def _(BVAdd, BVMul, Equals):
    def invariante(s):
        # x*y + z = a*b   (em BitVec: módulo 2^N)
        return Equals(BVAdd(BVMul(s['x'], s['y']), s['z']), BVMul(s['a'], s['b']))
 
    return (invariante,)
 
 
@app.cell
def _(declare, init, invariante, kinduction_always, trans):
    for _k in range(1, 4):
        kinduction_always(declare, init, trans, invariante, _k)
    return
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Resultados
 
    | $k$ | resultado |
    |---|---|
    | 1 | o **passo** falha |
    | 2 | **verificado** |
 
    Com $k = 1$ o contra-exemplo do passo é um estado **inalcançável**, por exemplo `pc = LEFT` com $y$ ímpar. A guarda de `skip → left` exige $y$ par, mas a indução simples parte de qualquer estado que satisfaça $\varphi$; aí $y \gg 1$ perde um bit 1 e $\varphi$ deixa de valer no estado seguinte. Com $k = 2$, o estado anterior ao `left` tem de ser um `skip` com $y$ par (e com $\varphi$), o que elimina o contra-exemplo.
 
    **Porque é que o invariante se mantém.** Cada transição preserva $x*y + z$:
 
    - `left`: $(2x)\cdot(y/2) + z = x*y + z$, pois $y$ é par;
    - `right`: $x\cdot(y-1) + (z + x) = x*y + z$.
 
    Estas identidades valem em aritmética módulo $2^n$, por isso o invariante não precisa de ausência de overflow. As transições para `error` não alteram `x`, `y`, `z`, pelo que $\varphi$ também vale em `error`.
 
    **Teste de controlo.** Com um invariante falso ($x*y + z = a*b + 1$) a verificação falha logo na base.
    """)
    return
 
 
@app.cell
def _(BVAdd, BVMul, Equals, bv, declare, init, kinduction_always, trans):
    _errado = lambda s: Equals(BVAdd(BVMul(s['x'], s['y']), s['z']),
                               BVAdd(BVMul(s['a'], s['b']), bv(1)))
    for _k in range(1, 4):
        kinduction_always(declare, init, trans, _errado, _k)
    return
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## 3. Segurança com $a, b < 2^{n/2}$
 
    $$
    \mathit{init}_3(s) \;\equiv\; \mathit{init}(s) \,\wedge\, a < 2^{n/2} \,\wedge\, b < 2^{n/2}
    $$
 
    ### Porque é que $\varphi$ do ponto 2 não chega
 
    O invariante do ponto 2 vale módulo $2^n$: pode valer em estados onde $x*y + z$ "deu a volta" e coincide com $a*b$, e nesses estados nada impede o overflow. Exemplo com $a = b = 1$: o estado `pc = RIGHT, x = 200, y = 1, z = 57` tem $200 + 57 = 257 \equiv 1 = a*b \pmod{256}$, mas $z + x = 257$ não cabe em 8 bits e vai para `error`. O estado é inalcançável, mas o passo da indução não o distingue.
 
    ### Invariante auxiliar
 
    $$
    \psi(s) \;\equiv\; pc \neq \mathit{ERROR} \;\wedge\; a < 2^{n/2} \;\wedge\; b < 2^{n/2} \;\wedge\; x*y + z = a*b \;\text{ (em } 2n \text{ bits)}
    $$
 
    A igualdade é calculada **alargando** os vetores para $2n$ bits (`BVZExt`). Como $x*y + z \leq (2^n-1)^2 + (2^n-1) < 2^{2n}$, não há volta e a igualdade é a verdadeira, em inteiros.
    """)
    return
 
 
@app.cell
def _(And, BVAdd, BVMul, BVULT, BVZExt, Equals, N, Not, bv, error, init):
    LIM = bv(2 ** (N // 2))          # 2^(n/2)
 
 
    def pre(s):
        # pré-condição: (a < 2^(n/2)) /\ (b < 2^(n/2))
        return And(BVULT(s['a'], LIM), BVULT(s['b'], LIM))
 
 
    def init3(s):
        return And(init(s), pre(s))
 
 
    def prod_inteiro(s):
        # x*y + z calculado em 2N bits (sem "voltas") e a*b também
        ext = lambda v: BVZExt(v, N)
        lhs = BVAdd(BVMul(ext(s['x']), ext(s['y'])), ext(s['z']))
        rhs = BVMul(ext(s['a']), ext(s['b']))
        return Equals(lhs, rhs)
 
 
    def inv_seguranca(s):
        return And(Not(error(s)), pre(s), prod_inteiro(s))
 
    return init3, inv_seguranca
 
 
@app.cell
def _(declare, init3, inv_seguranca, kinduction_always, trans):
    for _k in range(1, 4):
        kinduction_always(declare, init3, trans, inv_seguranca, _k)
    return
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Porque implica a ausência de erro
 
    Se $\psi$ vale, então $a*b < 2^{n/2}\cdot 2^{n/2} = 2^n$ e $x*y + z = a*b < 2^n$. Assim:
 
    - em `left` temos $y \geq 2$ (par e $\neq 0$), logo $2x \leq x*y \leq a*b < 2^n$ e não há overflow em $x \ll 1$;
    - em `right` temos $y \geq 1$, logo $z + x \leq z + x*y = a*b < 2^n$ e não há overflow em $z + x$.
 
    Portanto as transições para `error` nunca estão ativas.
 
    ### Resultado
 
    Com $\mathit{init}_3$ e $\psi$, a $k$-indução **verifica-se com $k = 2$**. Com $k = 1$ o passo falha por um estado inalcançável do segundo tipo, por exemplo `pc = RIGHT` com $y = 0$ (a guarda de `skip → right` exige $y \neq 0$), onde $y - 1$ dá a volta. Como $\psi$ inclui $pc \neq \mathit{ERROR}$, fica provado que, com este estado inicial, o estado de erro nunca é acessível.
 
    ### Teste de controlo
 
    Sem a pré-condição, $pc \neq \mathit{ERROR}$ **não** é verdadeira: a base falha com contra-exemplos reais (por exemplo $a = 36,\, b = 128$: $x$ passa de $36$ a $72$ e a $144$ e o `left` seguinte dá overflow). A pré-condição é necessária.
    """)
    return
 
 
@app.cell
def _(Not, declare, error, init, kinduction_always, trans):
    for _k in (1, 5, 9):
        kinduction_always(declare, init, trans, lambda s: Not(error(s)), _k)
    return
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## 4. Terminação (propriedade de animação)
 
    Sem pré-condição sobre `a` e `b`, o overflow é um fim possível do programa, por isso a terminação escreve-se
 
    $$
    F\,\big(G\,(pc = \mathit{STOP} \,\vee\, pc = \mathit{ERROR})\big)
    $$
 
    (Com $\mathit{init}_3$ e o ponto 3 podia escrever-se $F\,(G\,(pc = \mathit{STOP}))$, trocando apenas o predicado `terminal`.)
 
    ### Método do variante
 
    Procura-se $V(s)$ tal que:
 
    1. $V(s) \geq 0$;
    2. em cada transição, $V(s') < V(s) \,\vee\, V(s') = 0$;
    3. $V(s) = 0 \rightarrow pc = \mathit{STOP} \vee pc = \mathit{ERROR}$.
 
    Então $V$ chega a 0 em tempo finito e, a partir de 0, fica a 0 (a condição 2 só permite $V' = 0$), logo o sistema fica num estado terminal.
 
    ### Escolha do variante
 
    $y$ sozinho não serve: não muda em `init → skip` nem em `skip → left/right`; no `error` pode ser diferente de 0 e ficar constante; e $V = 0$ aparece em `skip` com $y = 0$, onde o programa ainda não parou. O variante depende do `pc`:
 
    | nodo | $V$ |
    |---|---|
    | `STOP`, `ERROR` | $0$ |
    | `SKIP` | $2y + 1$ |
    | `LEFT`, `RIGHT` | $2y$ |
    | `INIT` | $2b + 2$ |
 
    | transição | $V$ antes $\to$ depois |
    |---|---|
    | `init → skip` ($y' = b$) | $2b+2 \to 2b+1$ |
    | `skip → left/right` | $2y+1 \to 2y$ |
    | `skip → stop` ($y = 0$) | $1 \to 0$ |
    | `left → skip` ($y' = y/2$, $y \geq 2$) | $2y \to y+1 < 2y$ |
    | `right → skip` ($y' = y-1$) | $2y \to 2y - 1$ |
    | `left/right → error` | $\to 0$ |
    | `stop → stop`, `error → error` | $0 \to 0$ |
 
    O variante é calculado em $2n$ bits, porque $2b + 2$ pode chegar a $2^{n+1}$. Com `BitVec` sem sinal, a condição 1 é automática.
    """)
    return
 
 
@app.cell
def _(
    BV,
    BVAdd,
    BVMul,
    BVULT,
    BVZExt,
    ERROR,
    Equals,
    INIT,
    Implies,
    Int,
    Ite,
    N,
    Or,
    SKIP,
    STOP,
):
    W = 2 * N          # largura usada no variante (evita overflow em 2*b+2)
 
 
    def terminal(s):
        return Or(Equals(s['pc'], Int(STOP)), Equals(s['pc'], Int(ERROR)))
 
 
    def variante(s):
        '''V = 0 em STOP/ERROR; 2y+1 em SKIP; 2b+2 em INIT; 2y em LEFT/RIGHT.'''
        y = BVZExt(s['y'], N)
        b = BVZExt(s['b'], N)
        um, dois = BV(1, W), BV(2, W)
        return Ite(terminal(s), BV(0, W),
               Ite(Equals(s['pc'], Int(SKIP)), BVAdd(BVMul(dois, y), um),
               Ite(Equals(s['pc'], Int(INIT)), BVAdd(BVMul(dois, b), dois),
                   BVMul(dois, y))))
 
 
    def decresce(V):
        '''Condição 2, para um par de estados (s, s'): V(s') < V(s) ou V(s') = 0.'''
        return lambda s, sn: Or(BVULT(V(sn), V(s)), Equals(V(sn), BV(0, W)))
 
 
    def zero_implica_terminal(V):
        '''Condição 3: V(s) = 0 -> pc = STOP ou pc = ERROR.'''
        return lambda s: Implies(Equals(V(s), BV(0, W)), terminal(s))
 
    return decresce, variante, zero_implica_terminal
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Verificação
 
    A condição 3 é um invariante sobre estados e verifica-se com `kinduction_always`. A condição 2 fala de transições, por isso `kinduction_transicoes` faz a $k$-indução sobre pares de estados consecutivos: a base cobre as $k$ primeiras transições de qualquer traço inicial e o passo assume a propriedade em $k$ transições consecutivas. Esta formulação substitui o "para todo o sucessor $s'$" por "em todas as transições dos traços", que é equivalente e evita quantificadores no Z3. Aqui o $k$ conta **transições**.
    """)
    return
 
 
@app.cell
def _(
    Not,
    Or,
    Solver,
    declare,
    decresce,
    init,
    kinduction_always,
    mostra,
    trans,
    variante,
    zero_implica_terminal,
):
    def kinduction_transicoes(declare, init, trans, prop, k, verbose=True):
        '''k-indução para propriedades sobre transições: G (trans(s,s') -> prop(s,s')).
        Equivale a 'para todo o sucessor s' de qualquer s alcançável', pois
        percorre todas as transições dos traços.'''
        # base: as k primeiras transições de qualquer traço inicial
        with Solver(name="z3") as s:
            S = [declare(i) for i in range(k + 1)]
            s.add_assertion(init(S[0]))
            for i in range(k):
                s.add_assertion(trans(S[i], S[i + 1]))
            s.add_assertion(Or([Not(prop(S[i], S[i + 1])) for i in range(k)]))
            if s.solve():
                if verbose:
                    print(f"k={k}: a BASE falha. Contra-exemplo:")
                    mostra(S, s.get_model())
                return False
        # passo: prop em k transições consecutivas => prop na seguinte
        with Solver(name="z3") as s:
            S = [declare(i) for i in range(k + 2)]
            for i in range(k + 1):
                s.add_assertion(trans(S[i], S[i + 1]))
            for i in range(k):
                s.add_assertion(prop(S[i], S[i + 1]))
            s.add_assertion(Not(prop(S[k], S[k + 1])))
            if s.solve():
                if verbose:
                    print(f"k={k}: o PASSO falha. Contra-exemplo:")
                    mostra(S, s.get_model())
                return False
        if verbose:
            print(f"k={k}: verificado por {k}-indução.")
        return True
 
 
    def verifica_terminacao(V=variante, kmax=4):
        '''Prova F(G (pc=STOP \\/ pc=ERROR)) pelo método do variante (sem pré-condição).'''
        print("Condição 1: V(s) >= 0 -> automática (BitVec sem sinal).")
        print("Condição 2: V decresce (ou chega a 0) em cada transição")
        r2 = any(kinduction_transicoes(declare, init, trans, decresce(V), k)
                 for k in range(1, kmax + 1))
        print("Condição 3: V = 0 -> pc = STOP ou pc = ERROR")
        r3 = any(kinduction_always(declare, init, trans, zero_implica_terminal(V), k)
                 for k in range(1, kmax + 1))
        print("RESULTADO:", "o programa termina para quaisquer a, b" if r2 and r3
              else "NÃO foi possível verificar a terminação")
        return r2 and r3
 
    return (verifica_terminacao,)
 
 
@app.cell
def _(verifica_terminacao):
    verifica_terminacao()
    return
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Resultados
 
    | condição | resultado |
    |---|---|
    | 1 | automática |
    | 2 | verificada, $k = 1$ (conta transições) |
    | 3 | verificada, $k = 1$ |
 
    $k = 1$ basta porque o passo já inclui a transição que leva ao estado em análise, o que exclui à partida os estados incoerentes com o fluxo de controlo (por exemplo `left` com $y = 0$).
 
    **Teste de controlo.** Com um variante errado, $V = y$, o verificador rejeita a condição 2 (em `init → skip` o variante não desce) e a condição 3 (com $b = 0$, $V = 0$ em `pc = INIT`).
    """)
    return
 
 
@app.cell
def _(BVZExt, N, verifica_terminacao):
    verifica_terminacao(lambda s: BVZExt(s['y'], N), kmax=2)
    return
 
 
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Conclusão
 
    O programa termina, a partir de qualquer $a$ e $b$, num estado terminal (`stop` ou `error`).
    """)
    return



@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Conversa com LLM
 
    https://claude.ai/share/75be6205-4323-4ab2-8d95-1aa28f3f9810
    """)
    return
 
 
if __name__ == "__main__":
    app.run()
 